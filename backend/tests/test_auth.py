"""Sign-up and sign-in: every account proves it owns its college mailbox (Microsoft or an emailed
code); the domain decides the account type; one email = one account; password logins take a second step."""

import pyotp
from sqlalchemy import text

import app.api.routes.auth as auth_routes
from app.db.database import engine
from app.core.mail import DEV_OUTBOX
from tests.conftest import PASSWORD, emailed_code, register as register_with_code

DETAILS = {"name": "Test", "password": PASSWORD, "phone": "98765 43210",
           "reg_no": "229301", "course": "B.Tech CSE", "interests": ["tech"]}


async def register(client, email):
    return await register_with_code(client, {**DETAILS, "email": email})


async def test_domain_decides_account_type(client):
    r = await register(client, "asha@muj.manipal.edu")
    assert r.status_code == 201 and r.json()["user"]["account_type"] == "student"
    assert r.json()["user"]["reg_no"] == "229301"

    r = await register(client, "rao@jaipur.manipal.edu")
    user = r.json()["user"]
    assert r.status_code == 201 and user["account_type"] == "faculty"
    assert user["reg_no"] is None and user["interests"] is None   # student-only fields are dropped


async def test_other_domains_cannot_sign_up(client):
    r = await register(client, "someone@gmail.com")
    assert r.status_code == 400 and "@muj.manipal.edu" in r.json()["detail"]
    config = (await client.get("/api/auth/config")).json()
    assert config["email_domains"] == {"student": ["muj.manipal.edu"], "faculty": ["jaipur.manipal.edu"]}
    assert config["microsoft_client_id"] is None   # not set up: the button stays hidden


async def test_sign_up_needs_the_emailed_code(client):
    await client.post("/api/auth/register/code", json={"email": "asha@muj.manipal.edu"})
    r = await client.post("/api/auth/register", json={**DETAILS, "email": "asha@muj.manipal.edu", "code": "000000"})
    assert r.status_code == 400 and "wrong or has expired" in r.json()["detail"]
    before = len([m for m in DEV_OUTBOX if m["to"] == "asha@muj.manipal.edu"])
    assert (await client.post("/api/auth/register/code", json={"email": "asha@muj.manipal.edu"})).status_code == 202
    assert len([m for m in DEV_OUTBOX if m["to"] == "asha@muj.manipal.edu"]) == before   # at most one a minute
    code = emailed_code("asha@muj.manipal.edu")
    assert (await client.post("/api/auth/register", json={**DETAILS, "email": "asha@muj.manipal.edu", "code": code})).status_code == 201


async def test_one_account_per_email_regardless_of_case(client):
    assert (await register(client, "Asha@MUJ.manipal.edu")).json()["user"]["email"] == "asha@muj.manipal.edu"
    r = await register(client, "asha@muj.manipal.edu")
    assert r.status_code == 400 and r.json()["detail"].startswith("Email already registered")


async def test_password_login_takes_a_second_step(client, signup):
    await signup("asha@muj.manipal.edu")
    assert (await client.post("/api/auth/login", json={"email": "asha@muj.manipal.edu", "password": "wrong-one"})).status_code == 401
    r = (await client.post("/api/auth/login", json={"email": "ASHA@muj.manipal.edu", "password": PASSWORD})).json()
    assert r["second_step"] == "email" and r["access_token"] is None
    bad = await client.post("/api/auth/login/verify", json={"challenge": r["challenge"], "code": "000000"})
    assert bad.status_code == 400
    ok = (await client.post("/api/auth/login/verify", json={
        "challenge": r["challenge"], "code": emailed_code("asha@muj.manipal.edu"), "remember": True})).json()
    assert ok["access_token"] and ok["device_token"]

    # A remembered browser skips the second step, until the password changes
    again = (await client.post("/api/auth/login", json={"email": "asha@muj.manipal.edu", "password": PASSWORD,
                                                         "device_token": ok["device_token"]})).json()
    assert again["access_token"] and again["second_step"] is None
    headers = {"Authorization": f"Bearer {again['access_token']}"}
    await client.post("/api/users/me/password", headers=headers, json={"current_password": PASSWORD, "new_password": "new-password-1"})
    later = (await client.post("/api/auth/login", json={"email": "asha@muj.manipal.edu", "password": "new-password-1",
                                                         "device_token": ok["device_token"]})).json()
    assert later["second_step"] == "email"


async def test_wrong_codes_are_capped(client, signup):
    await signup("asha@muj.manipal.edu")
    r = (await client.post("/api/auth/login", json={"email": "asha@muj.manipal.edu", "password": PASSWORD})).json()
    for _ in range(5):
        assert (await client.post("/api/auth/login/verify", json={"challenge": r["challenge"], "code": "000000"})).status_code == 400
    right = emailed_code("asha@muj.manipal.edu")
    r2 = await client.post("/api/auth/login/verify", json={"challenge": r["challenge"], "code": right})
    assert r2.status_code == 429   # even the right code: sign in with the password again


async def test_wrong_passwords_lock_the_account_for_a_while(client, signup):
    await signup("asha@muj.manipal.edu")
    nobody = await client.post("/api/auth/login", json={"email": "nobody@muj.manipal.edu", "password": "x"})
    wrong = await client.post("/api/auth/login", json={"email": "asha@muj.manipal.edu", "password": "x"})
    assert nobody.status_code == wrong.status_code == 401 and nobody.json() == wrong.json()   # no telling who exists
    for _ in range(4):
        await client.post("/api/auth/login", json={"email": "asha@muj.manipal.edu", "password": "x"})
    r = await client.post("/api/auth/login", json={"email": "asha@muj.manipal.edu", "password": PASSWORD})
    assert r.status_code == 429 and "Try again in" in r.json()["detail"]   # even the right password, for now


async def test_deactivated_accounts_are_shut_out(client, signup):
    headers = await signup("asha@muj.manipal.edu")
    dsw = await signup("dsw@jaipur.manipal.edu", "dsw")
    me = (await client.get("/api/users/me", headers=headers)).json()
    assert (await client.patch(f"/api/admin/dsw/accounts/{me['id']}/active", headers=headers, json={"is_active": False})).status_code == 403
    r = await client.patch(f"/api/admin/dsw/accounts/{me['id']}/active", headers=dsw, json={"is_active": False})
    assert r.status_code == 200 and r.json()["is_active"] is False
    assert (await client.get("/api/users/me", headers=headers)).status_code == 401          # signed out at once
    r = await client.post("/api/auth/login", json={"email": "asha@muj.manipal.edu", "password": PASSWORD})
    assert r.status_code == 403
    await client.patch(f"/api/admin/dsw/accounts/{me['id']}/active", headers=dsw, json={"is_active": True})
    assert (await client.get("/api/users/me", headers=headers)).status_code == 200


async def test_names_and_passwords(client):
    r = await register_with_code(client, {**DETAILS, "email": "asha@muj.manipal.edu", "name": "   "})
    assert r.status_code == 422
    r = await client.post("/api/auth/register", json={**DETAILS, "email": "ravi@muj.manipal.edu", "password": "short1", "code": "1"})
    assert r.status_code == 422 and "at least 8" in r.text


async def test_authenticator_app(client, signup):
    headers = await signup("asha@muj.manipal.edu")
    setup = (await client.post("/api/users/me/two-step/totp", headers=headers)).json()
    assert setup["uri"].startswith("otpauth://totp/CamPulse")
    r = await client.put("/api/users/me/two-step", headers=headers, json={"method": "totp", "secret": setup["secret"], "code": "000000"})
    assert r.status_code == 400
    now = pyotp.TOTP(setup["secret"]).now()
    assert (await client.put("/api/users/me/two-step", headers=headers,
                             json={"method": "totp", "secret": setup["secret"], "code": now})).json()["second_factor"] == "totp"
    r = (await client.post("/api/auth/login", json={"email": "asha@muj.manipal.edu", "password": PASSWORD})).json()
    assert r["second_step"] == "totp"
    ok = await client.post("/api/auth/login/verify", json={"challenge": r["challenge"], "code": pyotp.TOTP(setup["secret"]).now()})
    assert ok.status_code == 200 and ok.json()["access_token"]


async def test_microsoft_sign_in(client, monkeypatch):
    assert (await client.post("/api/auth/microsoft", json={"id_token": "x"})).status_code == 503   # not set up
    async with engine.begin() as conn:   # the DSW's records name this faculty member as club 1's coordinator
        await conn.execute(text("INSERT INTO coordinator_invites (club_id, email) VALUES (1, 'rao@jaipur.manipal.edu')"))

    async def fake_verify(token):   # Microsoft checked who they are
        return {"asha": {"preferred_username": "Asha@muj.manipal.edu", "name": "Asha Verma"},
                "rao": {"email": "rao@jaipur.manipal.edu", "name": "Dr. Meenakshi Rao"},
                "gmail": {"email": "x@gmail.com", "name": "X"}}[token]
    monkeypatch.setattr(auth_routes, "verify_microsoft_id_token", fake_verify)

    r = (await client.post("/api/auth/microsoft", json={"id_token": "asha"})).json()
    assert r["user"]["name"] == "Asha Verma" and r["user"]["account_type"] == "student"
    assert r["user"]["has_password"] is False and r["user"]["profile_complete"] is False
    headers = {"Authorization": f"Bearer {r['access_token']}"}
    me = (await client.patch("/api/users/me", headers=headers, json={"reg_no": "1", "course": "BBA", "phone": "9876543210"})).json()
    assert me["profile_complete"] is True
    r = await client.post("/api/auth/login", json={"email": "asha@muj.manipal.edu", "password": "anything"})
    assert r.status_code == 401 and "Sign in with Microsoft" in r.json()["detail"]   # same answer as a wrong password
    assert (await client.post("/api/users/me/password", headers=headers, json={"new_password": "alumni-later"})).json()["has_password"]

    faculty = (await client.post("/api/auth/microsoft", json={"id_token": "rao"})).json()["user"]
    assert [(x["role"], x["club_id"]) for x in faculty["club_roles"]] == [("faculty_coordinator", 1)]   # claimed
    assert (await client.post("/api/auth/microsoft", json={"id_token": "gmail"})).status_code == 403


async def test_tokens(client, signup):
    headers = await signup("asha@muj.manipal.edu")
    assert (await client.get("/api/users/me", headers=headers)).json()["club_roles"] == []
    assert (await client.get("/api/users/me")).status_code in (401, 403)
    bad = {"Authorization": "Bearer not-a-token"}
    assert (await client.get("/api/users/me", headers=bad)).status_code == 401
