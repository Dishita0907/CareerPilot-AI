"""Integration check; use an isolated PostgreSQL database via DATABASE_URL."""
from fastapi.testclient import TestClient
from app.main import app
with TestClient(app) as c:
    assert c.get("/api/status").json()["count"]>0
    auth={"Authorization":"Bearer "+c.post("/api/session").json()["token"]}
    other={"Authorization":"Bearer "+c.post("/api/session").json()["token"]}
    p=c.put("/api/profile",headers=auth,json=dict(goal="AI Engineer",location="Chicago",years=4,resume="Python, AWS, SQL, LLM")).json()
    assert "Python" in p["skills"]
    r=c.post("/api/ask",headers=auth,json={"text":"Find AI engineer roles"}); r.raise_for_status()
    out=r.json()
    assert len(out["jobs"])==5 and out["answer"]
    assert all(j["url"].startswith("https://") and j["id"] for j in out["jobs"])
    assert len(c.get("/api/workspace",headers=auth).json()["history"])==2
    assert c.get("/api/workspace",headers=other).json()["history"]==[]
    assert c.get("/api/workspace").status_code==401
    assert c.post("/api/resume",headers=auth,files={"file":("bad.pdf",b"bad")}).status_code==422
    print("PASS: ranking, source links, history, isolation, PDF rejection")
