"""Who may run what: club teams approved by the DSW, event authorization, moderation,
account types and the platform admin. One scenario per rule."""

import pytest
from sqlalchemy import text

from app.db.database import engine

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


# ── Working teams, yearly memberships, announcements ─────
@pytest.fixture
async def coordinator(client, signup, dsw):
    """Club 1's faculty coordinator."""
    headers = await signup("rao@jaipur.manipal.edu")
    await client.post("/api/admin/dsw/clubs/1/faculty", headers=dsw, json={"email": "rao@jaipur.manipal.edu"})
    return headers


async def make_working(client, student, owner, coordinator, club=1):
    """Join `club`, apply, get recommended by the owner and approved by the coordinator."""
    await client.post(f"/api/clubs/{club}/join", headers=student)
    assert (await client.post(f"/api/clubs/{club}/application", headers=student)).status_code == 201
    app = (await client.get(f"/api/clubs/{club}/applications", headers=owner)).json()["items"][0]["id"]
    assert (await client.patch(f"/api/clubs/{club}/applications/{app}", headers=owner, json={"action": "recommend"})).status_code == 204
    assert (await client.patch(f"/api/clubs/{club}/applications/{app}", headers=coordinator, json={"action": "approve"})).status_code == 204


async def test_working_team_applications(client, signup, owner, coordinator):
    student = await signup("asha@muj.manipal.edu")
    r = await client.post("/api/clubs/1/application", headers=student)
    assert r.status_code == 400 and "Join the club" in r.json()["detail"]
    await client.post("/api/clubs/1/join", headers=student)
    assert "isn't recruiting" in (await client.post("/api/clubs/1/application", headers=student)).json()["detail"]
    assert (await client.patch("/api/clubs/1/settings", headers=student, json={"recruiting": True})).status_code == 403
    assert (await client.patch("/api/clubs/1/settings", headers=owner, json={"recruiting": True})).json()["recruiting"]

    assert (await client.post("/api/clubs/1/application", headers=student)).status_code == 201
    assert (await client.post("/api/clubs/1/application", headers=student)).status_code == 400   # one at a time
    app = (await client.get("/api/clubs/1/applications", headers=owner)).json()["items"][0]["id"]
    url = f"/api/clubs/1/applications/{app}"
    assert (await client.patch(url, headers=coordinator, json={"action": "approve"})).status_code == 403   # not recommended yet
    assert (await client.patch(url, headers=owner, json={"action": "shortlist"})).status_code == 204
    assert (await client.patch(url, headers=owner, json={"action": "recommend"})).status_code == 204
    assert (await client.patch(url, headers=owner, json={"action": "approve"})).status_code == 403   # coordinator's call
    notes = (await client.get("/api/notifications", headers=coordinator)).json()["items"]
    assert notes[0]["kind"] == "app_review" and notes[0]["club_id"] == 1
    assert (await client.patch(url, headers=coordinator, json={"action": "approve"})).status_code == 204

    roles = {x["role"] for x in (await client.get("/api/users/me", headers=student)).json()["club_roles"]}
    assert roles == {"member", "working_member"}
    members = (await client.get("/api/clubs/1/members", headers=owner)).json()
    assert [m["is_working"] for m in members] == [True]
    # Working members are the team's people, not its managers
    assert (await client.post("/api/events", headers=student, json={**EVENT, "club_id": 1})).status_code == 403


async def test_working_members_one_club_unless_both_allow(client, signup, owner, coordinator, approve, dsw):
    student = await signup("asha@muj.manipal.edu")
    await client.patch("/api/clubs/1/settings", headers=owner, json={"recruiting": True})
    await make_working(client, student, owner, coordinator)

    owner2 = await signup("owner2@muj.manipal.edu")
    await client.post("/api/clubs/2/owner-request", headers=owner2, json={})
    await approve()
    await client.patch("/api/clubs/2/settings", headers=owner2, json={"recruiting": True})
    await client.post("/api/clubs/2/join", headers=student)
    r = await client.post("/api/clubs/2/application", headers=student)
    assert r.status_code == 400 and "other clubs' working teams" in r.json()["detail"]
    await client.patch("/api/clubs/2/settings", headers=owner2, json={"working_multi_club": True})
    r = await client.post("/api/clubs/2/application", headers=student)
    assert r.status_code == 400 and "IEEE Computer Society doesn't let" in r.json()["detail"]   # club 1 still says no
    await client.patch("/api/clubs/1/settings", headers=owner, json={"working_multi_club": True})
    assert (await client.post("/api/clubs/2/application", headers=student)).status_code == 201


async def test_roster_and_announcements_are_for_the_working_team(client, signup, owner, coordinator):
    worker = await signup("asha@muj.manipal.edu")
    supporter = await signup("ravi@muj.manipal.edu")
    await client.patch("/api/clubs/1/settings", headers=owner, json={"recruiting": True})
    await make_working(client, worker, owner, coordinator)
    await client.post("/api/clubs/1/join", headers=supporter)

    names_only = (await client.get("/api/clubs/1/roster", headers=supporter)).json()
    assert names_only["detailed"] is False and all(p["course"] is None and p["roles"] == [] for p in names_only["items"])
    detailed = (await client.get("/api/clubs/1/roster", headers=worker)).json()
    assert detailed["detailed"] is True
    assert {tuple(sorted(p["roles"])) for p in detailed["items"]} == {
        ("member", "working_member"), ("member",), ("owner",), ("faculty_coordinator",)}
    assert "email" not in detailed["items"][0] and "phone" not in detailed["items"][0]

    assert (await client.post("/api/clubs/1/announcements", headers=worker, json={"body": "hi"})).status_code == 403
    post = (await client.post("/api/clubs/1/announcements", headers=owner, json={"body": "Meeting at 5"})).json()["id"]
    assert [n["kind"] for n in (await client.get("/api/notifications", headers=worker)).json()["items"]] == ["announcement", "application"]
    assert (await client.get("/api/notifications", headers=supporter)).json()["items"] == []
    assert (await client.get("/api/clubs/1/announcements", headers=supporter)).status_code == 403

    base = f"/api/clubs/1/announcements/{post}"
    assert (await client.post(f"{base}/comments", headers=worker, json={"body": "On it"})).status_code == 201
    assert (await client.post(f"{base}/reactions", headers=worker, json={"emoji": "👍"})).json() == [{"emoji": "👍", "count": 1, "mine": True}]
    assert (await client.post(f"{base}/reactions", headers=worker, json={"emoji": "👍"})).json() == []   # toggles off
    assert (await client.post(f"{base}/reactions", headers=worker, json={"emoji": "💩"})).status_code == 400
    page = (await client.get("/api/clubs/1/announcements", headers=worker)).json()
    assert page["total"] == 1 and page["items"][0]["author_title"] == "President"
    assert [c["body"] for c in page["items"][0]["comments"]] == ["On it"]


async def test_memberships_end_with_the_academic_year(client, signup, owner, coordinator):
    student = await signup("asha@muj.manipal.edu")
    await client.patch("/api/clubs/1/settings", headers=owner, json={"recruiting": True})
    await make_working(client, student, owner, coordinator)
    async with engine.begin() as conn:   # last academic year ended
        await conn.execute(text("UPDATE club_roles SET expires_on = '2020-07-31' WHERE role IN ('member', 'working_member')"))
    await client.patch("/api/clubs/1/settings", headers=owner, json={"recruiting": False})

    assert (await client.get("/api/clubs/1")).json()["member_count"] == 0
    assert (await client.get("/api/users/me", headers=student)).json()["club_roles"] == []
    assert (await client.get("/api/clubs/1/announcements", headers=student)).status_code == 403
    r = await client.post("/api/clubs/1/join", headers=student)   # renew the membership
    assert r.json()["member_count"] == 1
    mine = (await client.post("/api/clubs/1/application", headers=student)).json()   # renewal, even with recruiting off
    assert mine["is_renewal"] is True and mine["status"] == "applied"


# ── Private clubs, leave requests, benefits ──────────────
async def test_private_clubs_hide_from_outsiders(client, signup, owner, dsw):
    member = await signup("asha@muj.manipal.edu")
    outsider = await signup("ravi@muj.manipal.edu")
    await client.post("/api/clubs/1/join", headers=member)
    past = (await client.post("/api/events", headers=owner, json={**EVENT, "club_id": 1, "start_date": "2020-01-01", "end_date": "2020-01-02"})).json()["id"]
    upcoming = (await client.post("/api/events", headers=owner, json={**EVENT, "club_id": 1})).json()["id"]
    assert (await client.patch("/api/clubs/1/settings", headers=member, json={"is_private": True})).status_code == 403
    assert (await client.patch("/api/clubs/1/settings", headers=dsw, json={"is_private": True})).json()["is_private"]
    assert (await client.patch("/api/clubs/1/settings", headers=dsw, json={"recruiting": True})).status_code == 403   # only privacy

    async def club_ids(h=None):
        return [c["id"] for c in (await client.get("/api/clubs", headers=h or {})).json()["items"]]

    async def event_ids(h=None):
        return {e["id"] for e in (await client.get("/api/events", headers=h or {})).json()["items"]}

    assert await club_ids() == [2] and await club_ids(outsider) == [2]
    assert set(await club_ids(member)) == {1, 2} and set(await club_ids(dsw)) == {1, 2}
    assert await event_ids() == {past} and await event_ids(member) == {past, upcoming}
    assert (await client.get("/api/clubs/1")).status_code == 200                  # the page and history stay
    assert (await client.get(f"/api/events/{upcoming}", headers=outsider)).status_code == 404
    assert (await client.post(f"/api/events/{upcoming}/register", headers=outsider)).status_code == 404
    assert (await client.post("/api/clubs/1/join", headers=outsider)).status_code == 403
    assert (await client.get("/api/clubs/1/roster", headers=outsider)).json()["items"] == []


async def test_leaving_needs_the_dsw(client, signup, owner, coordinator, dsw):
    student = await signup("asha@muj.manipal.edu")
    await client.patch("/api/clubs/1/settings", headers=owner, json={"recruiting": True})
    await make_working(client, student, owner, coordinator)

    r = await client.post("/api/clubs/2/leave", headers=student, json={"scope": "club"})
    assert r.status_code == 400 and "not in this club" in r.json()["detail"]
    assert (await client.post("/api/clubs/1/leave", headers=coordinator, json={"scope": "club"})).status_code == 400
    r = await client.post("/api/clubs/1/leave", headers=student, json={"scope": "working_team", "reason": "Exams"})
    assert r.status_code == 201 and r.json()["status"] == "pending"
    assert (await client.post("/api/clubs/1/leave", headers=student, json={"scope": "club"})).status_code == 400   # one at a time
    assert (await client.get("/api/admin/dsw/leave-requests", headers=student)).status_code == 403

    queue = (await client.get("/api/admin/dsw/leave-requests", headers=dsw)).json()["items"]
    assert [(q["club_name"], q["scope"], q["reason"]) for q in queue] == [("IEEE Computer Society", "working_team", "Exams")]
    assert (await client.patch(f"/api/admin/dsw/leave-requests/{queue[0]['id']}", headers=dsw, json={"action": "approve"})).status_code == 204
    roles = {x["role"] for x in (await client.get("/api/users/me", headers=student)).json()["club_roles"]}
    assert roles == {"member"}   # off the working team, still a member

    await client.post("/api/clubs/1/leave", headers=student, json={"scope": "club"})
    queue = (await client.get("/api/admin/dsw/leave-requests", headers=dsw)).json()["items"]
    await client.patch(f"/api/admin/dsw/leave-requests/{queue[0]['id']}", headers=dsw, json={"action": "approve"})
    assert (await client.get("/api/users/me", headers=student)).json()["club_roles"] == []
    assert (await client.get("/api/clubs/1")).json()["member_count"] == 0


async def test_benefits(client, signup, owner):
    student = await signup("asha@muj.manipal.edu")
    perk = dict(title="10% off fest passes", audience="members")
    assert (await client.post("/api/clubs/1/benefits", headers=student, json=perk)).status_code == 403
    assert (await client.post("/api/clubs/1/benefits", headers=owner, json=perk)).status_code == 201
    await client.post("/api/clubs/1/benefits", headers=owner, json={**perk, "title": "Old", "valid_until": "2020-01-01"})
    assert [b["title"] for b in (await client.get("/api/clubs/1/benefits")).json()] == ["10% off fest passes"]   # public, current only


async def test_for_you_ranking(client, signup, owner, dsw):
    student = await signup("asha@muj.manipal.edu")   # interests: none; joins club 1
    await client.post("/api/clubs/1/join", headers=student)
    other = await signup("acm@jaipur.manipal.edu")
    await client.post("/api/admin/dsw/clubs/2/faculty", headers=dsw, json={"email": "acm@jaipur.manipal.edu"})
    mine = (await client.post("/api/events", headers=owner, json={**EVENT, "club_id": 1, "title": "Mine"})).json()["id"]
    elsewhere = (await client.post("/api/events", headers=other, json={**EVENT, "club_id": 2, "title": "Elsewhere"})).json()["id"]
    gone = (await client.post("/api/events", headers=other, json={**EVENT, "club_id": 2, "start_date": "2020-01-01", "end_date": "2020-01-02"})).json()["id"]
    ranked = [e["id"] for e in (await client.get("/api/events/for-you", headers=student)).json()]
    assert ranked == [mine, elsewhere]                  # own club first; past events never
    await client.post(f"/api/events/{mine}/register", headers=student)
    assert [e["id"] for e in (await client.get("/api/events/for-you", headers=student)).json()] == [elsewhere]
    assert gone not in [e["id"] for e in (await client.get("/api/events/for-you")).json()]


# ── New club requests ────────────────────────────────────
CLUB_REQUEST = dict(name="Robotics Society", abbr="RoboSoc", description="Robots.", tags=["robotics"],
                    purpose="No hardware club yet.", plans="Two workshops.", contact_phone="9876543210",
                    coordinator_email="rao@jaipur.manipal.edu",
                    founding_emails=["ravi@muj.manipal.edu", "meera@muj.manipal.edu"])


async def test_new_club_requests(client, signup, dsw):
    student = await signup("asha@muj.manipal.edu")
    ravi = await signup("ravi@muj.manipal.edu")       # a founder with an account; meera hasn't signed up
    bad = await client.post("/api/club-requests", headers=student, json={**CLUB_REQUEST, "coordinator_email": "x@muj.manipal.edu"})
    assert bad.status_code == 400 and "faculty email" in bad.json()["detail"]
    r = await client.post("/api/club-requests", headers=student, json=CLUB_REQUEST)
    assert r.status_code == 201 and r.json()["status"] == "awaiting_coordinator" and not r.json()["coordinator_signed_up"]
    req = r.json()["id"]
    assert (await client.post("/api/club-requests", headers=student, json=CLUB_REQUEST)).status_code == 400   # one at a time

    # The coordinator signs up later: told about it, and only they can confirm
    faculty = await signup("rao@jaipur.manipal.edu")
    assert (await client.get("/api/notifications", headers=faculty)).json()["items"][0]["kind"] == "club_request"
    assert [x["id"] for x in (await client.get("/api/club-requests/for-me", headers=faculty)).json()] == [req]
    assert (await client.get("/api/club-requests/for-me", headers=faculty)).json()[0]["contact_phone"] is None
    assert (await client.patch(f"/api/club-requests/{req}", headers=dsw, json={"action": "approve"})).status_code == 400   # not yet
    assert (await client.patch(f"/api/club-requests/{req}", headers=ravi, json={"action": "confirm"})).status_code == 403
    assert (await client.patch(f"/api/club-requests/{req}", headers=faculty, json={"action": "confirm"})).status_code == 200

    queue = (await client.get("/api/club-requests", headers=dsw)).json()["items"]
    assert [x["name"] for x in queue] == ["Robotics Society"] and queue[0]["contact_phone"] == "9876543210"
    r = await client.patch(f"/api/club-requests/{req}", headers=dsw, json={"action": "approve"})
    assert r.status_code == 200 and r.json()["skipped"] == ["meera@muj.manipal.edu: hasn't signed up yet"]
    club = r.json()["club_id"]

    def roles(me):
        return {(x["role"], x["club_id"]) for x in me["club_roles"]}
    assert roles((await client.get("/api/users/me", headers=student)).json()) == {("owner", club), ("member", club)}
    assert roles((await client.get("/api/users/me", headers=ravi)).json()) == {("editor", club), ("member", club)}
    assert roles((await client.get("/api/users/me", headers=faculty)).json()) == {("faculty_coordinator", club)}
    assert (await client.get(f"/api/clubs/{club}")).json()["member_count"] == 2
