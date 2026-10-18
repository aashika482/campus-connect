"""Who may run what: club teams approved by the DSW, event authorization, moderation,
account types and the platform admin. One scenario per rule."""

import pytest

EVENT = dict(title="Hack", description="d", start_date="2030-01-01", end_date="2030-01-02",
             date_display="Jan 1", tags=["tech"])


@pytest.fixture
async def dsw(signup):
    return await signup("dsw@jaipur.manipal.edu", "dsw")


@pytest.fixture
def approve(client, dsw):
    """Approve the newest pending team request (optionally with a multi-club exception)."""
    async def _approve(exception: bool = False, action: str = "approve"):
        queue = (await client.get("/api/admin/dsw/club-roles", headers=dsw)).json()["items"]
        return await client.patch(f"/api/admin/dsw/club-roles/{queue[0]['id']}", headers=dsw,
                                  json={"action": action, "multi_club_exception": exception})
    return _approve


@pytest.fixture
async def owner(client, signup, approve):
    """An approved owner of club 1."""
    headers = await signup("owner@muj.manipal.edu")
    assert (await client.post("/api/clubs/1/owner-request", headers=headers, json={"title": "President"})).status_code == 201
    assert (await approve()).status_code == 200
    return headers


async def test_owner_needs_dsw_approval(client, signup, approve):
    me = await signup("asha@muj.manipal.edu")
    r = await client.post("/api/clubs/1/owner-request", headers=me, json={"title": "President"})
    assert r.status_code == 201 and r.json()["status"] == "pending"
    assert (await client.post("/api/events", headers=me, json={**EVENT, "club_id": 1})).status_code == 403
    assert (await client.get("/api/clubs/1/members", headers=me)).status_code == 403

    r = await approve()
    assert r.status_code == 200 and r.json()["status"] == "active"
    assert (await client.post("/api/events", headers=me, json={**EVENT, "club_id": 1})).status_code == 201
    roles = (await client.get("/api/users/me", headers=me)).json()["club_roles"]
    assert [(r["club_id"], r["role"], r["status"], r["title"]) for r in roles] == [(1, "owner", "active", "President")]


async def test_team_only_runs_its_own_club(client, signup, owner):
    other = await signup("other@muj.manipal.edu")
    acm_event = (await client.post("/api/events", headers=owner, json={**EVENT, "club_id": 1})).json()["id"]

    assert (await client.post("/api/events", headers=owner, json={**EVENT, "club_id": 2})).status_code == 403
    for method, url in [("patch", f"/api/events/{acm_event}"), ("delete", f"/api/events/{acm_event}"),
                        ("get", f"/api/events/{acm_event}/registrations"), ("get", "/api/clubs/1/members"),
                        ("get", "/api/discussions/admin/feed?club_id=1"), ("post", "/api/uploads/signature")]:
        kwargs = {"json": {"title": "x"}} if method == "patch" else {}
        r = await getattr(client, method)(url, headers=other, **kwargs)
        assert r.status_code == 403, (method, url, r.status_code)
    assert (await client.patch(f"/api/events/{acm_event}", headers=owner, json={"title": "Renamed"})).status_code == 200


async def test_one_owner_per_club_and_editor_limit(client, signup, owner, approve):
    rival = await signup("rival@muj.manipal.edu")
    r = await client.post("/api/clubs/1/owner-request", headers=rival, json={})
    assert r.status_code == 400 and "already has an owner" in r.json()["detail"]

    await signup("ed1@muj.manipal.edu")
    await signup("ed2@muj.manipal.edu")
    for email in ("ed1@muj.manipal.edu", "ed2@muj.manipal.edu"):
        assert (await client.post("/api/clubs/1/editors", headers=owner, json={"email": email})).status_code == 201
    assert (await approve()).status_code == 200                 # ed2 (newest first): fills the 1 editor slot
    r = await approve()
    assert r.status_code == 409 and "limit" in r.json()["detail"]

    # Only the owner/editors propose, and only existing student accounts
    assert (await client.post("/api/clubs/1/editors", headers=rival, json={"email": "rival@muj.manipal.edu"})).status_code == 403
    assert (await client.post("/api/clubs/1/editors", headers=owner, json={"email": "nobody@muj.manipal.edu"})).status_code == 404


async def test_approving_an_owner_rejects_rival_requests(client, signup, approve, dsw):
    for email in ("a@muj.manipal.edu", "b@muj.manipal.edu"):
        headers = await signup(email)
        assert (await client.post("/api/clubs/2/owner-request", headers=headers, json={})).status_code == 201
    assert (await approve()).status_code == 200   # the newest one (b) becomes owner
    rejected = (await client.get("/api/admin/dsw/club-roles?status=rejected", headers=dsw)).json()["items"]
    assert [(r["email"], r["role"]) for r in rejected] == [("a@muj.manipal.edu", "owner")]
    assert (await client.get("/api/admin/dsw/club-roles", headers=dsw)).json()["total"] == 0


async def test_second_club_needs_a_dsw_exception(client, signup, owner, approve):
    r = await client.post("/api/clubs/2/owner-request", headers=owner, json={})
    assert r.status_code == 201
    r = await approve()
    assert r.status_code == 409 and "multi-club exception" in r.json()["detail"]
    r = await approve(exception=True)
    assert r.status_code == 200 and r.json()["multi_club_exception"] is True


async def test_ending_a_role_removes_access_immediately(client, signup, owner, approve, dsw):
    team = (await client.get("/api/admin/dsw/club-roles?status=active", headers=dsw)).json()["items"]
    r = await client.patch(f"/api/admin/dsw/club-roles/{team[0]['id']}", headers=dsw, json={"action": "end"})
    assert r.status_code == 200 and r.json()["status"] == "ended"
    assert (await client.post("/api/events", headers=owner, json={**EVENT, "club_id": 1})).status_code == 403
    assert (await client.get("/api/users/me", headers=owner)).json()["club_roles"] == []   # ended = history only


async def test_faculty_coordinators_are_assigned_by_the_dsw(client, signup, dsw):
    faculty = await signup("rao@jaipur.manipal.edu")
    await signup("asha@muj.manipal.edu")
    r = await client.post("/api/admin/dsw/clubs/1/faculty", headers=dsw, json={"email": "asha@muj.manipal.edu"})
    assert r.status_code == 400   # students can't coordinate
    r = await client.post("/api/admin/dsw/clubs/1/faculty", headers=dsw, json={"email": "rao@jaipur.manipal.edu"})
    assert r.status_code == 201 and r.json()["status"] == "active"
    assert (await client.post("/api/events", headers=faculty, json={**EVENT, "club_id": 1})).status_code == 201
    assert (await client.post("/api/admin/dsw/clubs/1/faculty", headers=faculty, json={"email": "rao@jaipur.manipal.edu"})).status_code == 403


async def test_moderation(client, signup, owner, dsw):
    student = await signup("asha@muj.manipal.edu")
    other_team = await signup("acm@jaipur.manipal.edu")
    await client.post("/api/admin/dsw/clubs/2/faculty", headers=dsw, json={"email": "acm@jaipur.manipal.edu"})
    event = (await client.post("/api/events", headers=owner, json={**EVENT, "club_id": 1})).json()["id"]

    async def comment():
        return (await client.post(f"/api/discussions/{event}", headers=student, json={"content": "hi"})).json()["id"]

    c = await comment()
    notes = (await client.get("/api/notifications", headers=owner)).json()["items"]
    assert [n["kind"] for n in notes] == ["comment"]   # the team hears about new comments
    assert (await client.delete(f"/api/discussions/{event}/{c}", headers=other_team)).status_code == 403
    assert (await client.delete(f"/api/discussions/{event}/{c}", headers=owner)).status_code == 204
    c = await comment()
    assert (await client.delete(f"/api/discussions/{event}/{c}", headers=dsw)).status_code == 204
    r = await client.post(f"/api/discussions/{event}", headers=owner, json={"content": "official"})
    assert r.json()["is_official"] is True


async def test_only_students_join_and_nobody_leaves(client, signup):
    student = await signup("asha@muj.manipal.edu")
    faculty = await signup("rao@jaipur.manipal.edu")
    r = await client.post("/api/clubs/1/join", headers=student)
    assert r.status_code == 200 and r.json()["member_count"] == 1
    assert (await client.post("/api/clubs/1/join", headers=student)).json()["member_count"] == 1   # idempotent
    assert (await client.post("/api/clubs/1/join", headers=faculty)).status_code == 403
    assert (await client.delete("/api/clubs/1/join", headers=student)).status_code == 405


async def test_graduation_ends_team_roles_but_keeps_membership(client, signup, owner, dsw):
    await client.post("/api/clubs/1/join", headers=owner)
    me = (await client.get("/api/users/me", headers=owner)).json()
    r = await client.patch(f"/api/admin/dsw/accounts/{me['id']}", headers=dsw, json={"account_type": "alumni"})
    assert r.status_code == 200 and r.json()["account_type"] == "alumni"
    roles = (await client.get("/api/users/me", headers=owner)).json()["club_roles"]
    assert [(x["role"], x["status"]) for x in roles] == [("member", "active")]
    assert (await client.post("/api/events", headers=owner, json={**EVENT, "club_id": 1})).status_code == 403


async def test_dsw_and_platform_admin_have_separate_powers(client, signup, dsw):
    tech = await signup("tech@jaipur.manipal.edu", "platform_admin")
    student = await signup("asha@muj.manipal.edu")
    me = (await client.get("/api/users/me", headers=student)).json()

    # Only the platform admin appoints DSW accounts; the DSW can't touch DSW / admin accounts
    assert (await client.post("/api/admin/platform/dsw-accounts", headers=dsw, json={"email": "asha@muj.manipal.edu"})).status_code == 403
    r = await client.post("/api/admin/platform/dsw-accounts", headers=tech, json={"email": "asha@muj.manipal.edu"})
    assert r.status_code == 201 and r.json()["account_type"] == "dsw"
    assert (await client.patch(f"/api/admin/dsw/accounts/{me['id']}", headers=dsw, json={"account_type": "student"})).status_code == 403
    r = await client.delete(f"/api/admin/platform/dsw-accounts/{me['id']}", headers=tech)
    assert r.json()["account_type"] == "student"   # back to what the email domain gives

    # The platform admin has no business authority
    assert (await client.get("/api/admin/dsw/club-roles", headers=tech)).status_code == 403
    assert (await client.patch("/api/admin/dsw/events/1/hot", headers=tech, json={"is_hot": True})).status_code == 403
    assert (await client.post("/api/clubs", headers=tech, json=dict(name="X", abbr="X", description="d", tags=["t"]))).status_code == 403

    # Both read the audit log; nobody else does
    log = (await client.get("/api/admin/audit-log", headers=tech)).json()["items"]
    assert [e["action"] for e in log] == ["user.remove_dsw", "user.grant_dsw"]
    assert (await client.get("/api/admin/audit-log", headers=dsw)).status_code == 200
    assert (await client.get("/api/admin/audit-log", headers=student)).status_code == 403
