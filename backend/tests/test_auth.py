"""Sign-up and sign-in: college domains decide the account type, one email = one account."""

from tests.conftest import PASSWORD


async def register(client, email):
    return await client.post("/api/auth/register", json={
        "name": "Test", "email": email, "password": PASSWORD, "phone": "98765 43210",
        "reg_no": "229301", "course": "B.Tech CSE", "interests": ["tech"],
    })


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
    assert config == {"email_domains": {"student": ["muj.manipal.edu"], "faculty": ["jaipur.manipal.edu"]}}


async def test_one_account_per_email_regardless_of_case(client):
    assert (await register(client, "Asha@MUJ.manipal.edu")).json()["user"]["email"] == "asha@muj.manipal.edu"
    r = await register(client, "asha@muj.manipal.edu")
    assert r.status_code == 400 and r.json()["detail"] == "Email already registered"

    r = await client.post("/api/auth/login", json={"email": "ASHA@muj.manipal.edu", "password": PASSWORD})
    assert r.status_code == 200
    r = await client.post("/api/auth/login", json={"email": "asha@muj.manipal.edu", "password": "wrong-one"})
    assert r.status_code == 401


async def test_tokens(client, signup):
    headers = await signup("asha@muj.manipal.edu")
    assert (await client.get("/api/users/me", headers=headers)).json()["club_roles"] == []
    assert (await client.get("/api/users/me")).status_code in (401, 403)
    bad = {"Authorization": "Bearer not-a-token"}
    assert (await client.get("/api/users/me", headers=bad)).status_code == 401
