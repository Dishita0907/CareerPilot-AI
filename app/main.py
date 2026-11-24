import hashlib
import os
import secrets
from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path

import psycopg
from fastapi import FastAPI, Header, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from psycopg.types.json import Jsonb
from pydantic import BaseModel, Field
from pypdf import PdfReader

from .agent import workflow
from .search import DATA
from .skills import skills

def connect():
    return psycopg.connect(os.environ["DATABASE_URL"],connect_timeout=5)

@asynccontextmanager
async def lifespan(app):
    with connect() as db:
        db.execute("CREATE TABLE IF NOT EXISTS profiles (id text PRIMARY KEY, profile jsonb NOT NULL)")
        db.execute("""CREATE TABLE IF NOT EXISTS messages (id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                   owner text REFERENCES profiles(id) ON DELETE CASCADE, role text NOT NULL, body text NOT NULL)""")
        db.execute("CREATE INDEX IF NOT EXISTS owner_history ON messages(owner,id)")
    yield

app=FastAPI(title="CareerPilot AI",lifespan=lifespan)
EMPTY={"goal":"","location":"","years":None,"skills":[]}

class Profile(BaseModel):
    goal:str=Field(max_length=300)
    location:str=Field(default="",max_length=120)
    years:float|None=Field(default=None,ge=0,le=80)
    resume:str|None=Field(default=None,max_length=80000)

class Question(BaseModel):
    text:str=Field(min_length=1,max_length=1500)

def key(token):
    return hashlib.sha256(token.encode()).hexdigest()

def load(db,auth,lock=False):
    token=auth.removeprefix("Bearer ")
    row=db.execute("SELECT profile FROM profiles WHERE id=%s"+(" FOR UPDATE" if lock else ""),(key(token),)).fetchone()
    if not row:
        raise HTTPException(401,"Workspace expired or missing")
    return key(token),row[0]

def history(db,owner):
    rows=db.execute("SELECT role,body FROM messages WHERE owner=%s ORDER BY id DESC LIMIT 40",(owner,)).fetchall()
    return [dict(role=r,text=b) for r,b in reversed(rows)]

@app.get("/api/status")
def status():
    return dict(count=len(DATA["jobs"]),date=DATA["retrieved"],mode="OpenAI advisor" if os.getenv("OPENAI_API_KEY") else "Local matching")

@app.post("/api/session")
def session():
    token=secrets.token_urlsafe(32)
    with connect() as db:
        db.execute("INSERT INTO profiles VALUES (%s,%s)",(key(token),Jsonb(EMPTY)))
    return {"token":token}

@app.get("/api/workspace")
def workspace(authorization:str=Header(default="")):
    with connect() as db:
        owner,profile=load(db,authorization)
        return dict(profile=profile,history=history(db,owner))

@app.put("/api/profile")
def save(body:Profile,authorization:str=Header(default="")):
    with connect() as db:
        owner,old=load(db,authorization,True)
        profile=body.model_dump(exclude={"resume"})
        profile["skills"]=old["skills"] if body.resume is None else skills(body.resume)
        db.execute("UPDATE profiles SET profile=%s WHERE id=%s",(Jsonb(profile),owner))
        return profile

@app.post("/api/resume")
def extract(file:UploadFile,authorization:str=Header(default="")):
    with connect() as db:
        load(db,authorization)
    raw=file.file.read(2_000_001)
    if len(raw)>2_000_000:
        raise HTTPException(413,"PDF exceeds 2 MB")
    try:
        reader=PdfReader(BytesIO(raw))
        if len(reader.pages)>20:
            raise HTTPException(422,"Use a résumé of 20 pages or fewer")
        text=" ".join(page.extract_text() or "" for page in reader.pages)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(422,"Unable to read this PDF")
    if not text.strip():
        raise HTTPException(422,"Paste the text from your scanned résumé")
    return {"text":text[:80000]}

@app.post("/api/ask")
def ask(body:Question,authorization:str=Header(default="")):
    with connect() as db:
        owner,profile=load(db,authorization,True)
        try:
            result=workflow.invoke(dict(profile=profile,question=body.text,history=history(db,owner)))
        except Exception as exc:
            raise HTTPException(503,"Advisor unavailable. Check model configuration and retry.") from exc
        with db.cursor() as cur:
            cur.executemany("INSERT INTO messages(owner,role,body) VALUES (%s,%s,%s)",
                [(owner,"user",body.text),(owner,"assistant",result["answer"])])
        return {"jobs":result["jobs"],"answer":result["answer"]}

dist=Path(__file__).resolve().parents[1]/"web/dist"
if dist.is_dir():
    app.mount("/",StaticFiles(directory=dist,html=True),name="web")
