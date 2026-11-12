"""Raccoglie le notizie delle ultime 24-48h da Google News RSS per ogni sezione di fonti.json.
Uso: python3 rassegna/fetch_news.py OUT.json"""
import json, sys, time, urllib.parse, urllib.request, re, html
from datetime import datetime, timezone, timedelta
import feedparser

BASE = "https://news.google.com/rss/search?"
HERE = __file__.rsplit('/', 1)[0]

def gnews(q):
    lang = {"hl": "it", "gl": "IT", "ceid": "IT:it"}
    if q.endswith("|en"):
        q, lang = q[:-3], {"hl": "en-GB", "gl": "GB", "ceid": "GB:en"}
    url = BASE + urllib.parse.urlencode({"q": q, **lang})
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (rassegna-bot)"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return feedparser.parse(r.read())

def norm(t):
    return re.sub(r"\W+", " ", t.lower()).strip()

def main(out):
    cfg = json.load(open(f"{HERE}/fonti.json"))
    cutoff = datetime.now(timezone.utc) - timedelta(hours=36)
    seen, result = set(), {}
    for sez in cfg["sezioni"]:
        items = []
        for q in sez["query"]:
            try:
                feed = gnews(q)
            except Exception as e:
                print(f"! {q}: {e}", file=sys.stderr); continue
            for e in feed.entries[:15]:
                pub = datetime(*e.published_parsed[:6], tzinfo=timezone.utc) if e.get("published_parsed") else None
                if pub and pub < cutoff: continue
                src = e.get("source", {}).get("title", "")
                title = html.unescape(e.title.rsplit(" - ", 1)[0]) if src else html.unescape(e.title)
                k = norm(title)[:80]
                if k in seen: continue
                seen.add(k)
                items.append({"titolo": title, "fonte": src, "link": e.link,
                              "data": pub.isoformat() if pub else None, "query": q})
            time.sleep(0.5)
        items.sort(key=lambda x: x["data"] or "", reverse=True)
        result[sez["id"]] = {"titolo": sez["titolo"], "notizie": items[:30]}
        print(f"{sez['id']}: {len(items)}", file=sys.stderr)
    json.dump({"generato": datetime.now(timezone.utc).isoformat(), "sezioni": result},
              open(out, "w"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "news.json")
