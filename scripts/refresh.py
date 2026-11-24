"""Refresh the real-job snapshot atomically. Run from the project root."""
import argparse
import datetime as dt
import html
import json
from pathlib import Path
import re
import sys
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.skills import skills

URL = "https://boards-api.greenhouse.io/v1/boards/stripe/jobs?content=true"
DEST = Path(__file__).resolve().parents[1] / "data/jobs.json"
def clean(raw):
    raw = re.sub(r"</(?:p|li|h[1-6])>", "\n", html.unescape(raw), flags=re.I)
    return html.unescape(re.sub("<[^>]+>", "", raw))

def collect(feed):
    records = []
    for j in feed["jobs"]:
        if j.get("language") not in ("en", None) or not j.get("content"):
            continue
        body = clean(j["content"])
        parts = re.split(r"minimum (?:requirements|qualifications)", body, flags=re.I)
        minimum = re.split(r"preferred (?:requirements|qualifications)|nice to have", parts[-1], flags=re.I)[0] if len(parts)>1 else ""
        years = re.search(r"\b(\d{1,2})(?:\s*[-–]\s*\d{1,2})?\+?\s+years?\b",minimum,re.I)
        records.append(dict(id=str(j["id"]),title=j["title"].strip(),company="Stripe",location=j["location"]["name"],
            url=j["absolute_url"],updated=j["updated_at"],skills=skills(minimum),years=int(years[1]) if years else None))
    records.sort(key=lambda j:j["id"])
    return records

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--feed",type=Path,help="Previously downloaded Greenhouse JSON")
    args=parser.parse_args()
    if args.feed:
        feed=json.loads(args.feed.read_bytes())
    else:
        with urlopen(URL,timeout=90) as response:
            feed=json.load(response)
    records=collect(feed)
    if not records or len({j["id"] for j in records})!=len(records):
        raise ValueError("Incomplete or duplicate job feed")
    payload=dict(source=URL,retrieved=dt.datetime.now(dt.timezone.utc).date().isoformat(),jobs=records)
    tmp=DEST.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload,ensure_ascii=False,separators=(",",":")))
    tmp.replace(DEST)
    print(f"Saved {len(records)} real postings")
