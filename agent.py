import asyncio, json, re, sys, html as H, webbrowser
from bs4 import BeautifulSoup
from dnotifier import DNotifier
from config import APP_ID, SECRET
from scanner import scan, fetch

PROVIDER = "openai"
MODEL = "gpt-4o-mini"
MAX_TRIES = 3
MAX_ISSUES = 12

def norm(h):
    return str(BeautifulSoup(h, "html.parser"))

async def ask_ai(n, issue, snippet, feedback):
    prompt = (
        "You are a web accessibility expert. Fix this HTML element so it passes the "
        f"accessibility check '{issue['type']}'. Keep its other attributes. "
        "Reply with ONLY JSON like "
        '{"fixed_html": "<fixed element>", "explanation": "one short sentence"}.\n'
        f"HTML: {snippet[:1500]}\n{feedback}"
    )
    r = await n.send_ai(sender_id="maryam", message={"text": prompt},
                        provider=PROVIDER, model=MODEL, save_history=False)
    d = r.get("data", r)
    if d.get("type") == "error":
        raise RuntimeError(d.get("message"))
    text = d.get("content", "")
    a, b = text.find("{"), text.rfind("}")
    return json.loads(text[a:b + 1])

async def run(url):
    current = norm(fetch(url))
    original = current
    start = scan(current)
    print(f"\n[Agent] {len(start)} issues mile. Pehle {min(len(start), MAX_ISSUES)} fix karunga.\n")

    n = DNotifier(app_id=APP_ID, secret=SECRET, transport="http", user_id="maryam")
    await n.connect()

    results = []
        picked, seen = [], {}
    for i in start:
        if seen.get(i["type"], 0) < 4:
            picked.append(i)
            seen[i["type"]] = seen.get(i["type"], 0) + 1
    picked = picked[:MAX_ISSUES]
    for issue in picked:
        snippet = issue["html"]
        if snippet not in current:
            continue
        item = {"type": issue["type"], "before": snippet, "after": "", "why": "",
                "tries": 0, "ok": False}
        feedback = ""
        for attempt in range(1, MAX_TRIES + 1):
            item["tries"] = attempt
            try:
                if issue["type"] == "html-lang":
                    candidate = current.replace("<html", '<html lang="en"', 1)
                    item["after"], item["why"] = '<html lang="en">', "Rule-based fix (no AI): page language set."
                else:
                    fix = await ask_ai(n, issue, snippet, feedback)
                    candidate = norm(current.replace(snippet, fix["fixed_html"], 1))
                    item["after"], item["why"] = fix["fixed_html"], fix.get("explanation", "")
            except Exception as e:
                print(f"[Agent] {issue['type']} try {attempt}: AI error: {e}")
                feedback = "Previous reply was invalid. Reply with valid JSON only."
                continue
            before_n, after_n = len(scan(current)), len(scan(candidate))
            print(f"[Agent] {issue['type']} try {attempt}: issues {before_n} -> {after_n}")
            if after_n < before_n:
                current, item["ok"] = candidate, True
                break
            feedback = (f"Your previous fix did not work (issue still reported): "
                        f"{item['after'][:300]}. Try a different approach.")
        results.append(item)

    final = len(scan(current))
    print(f"\n[Agent] Khatam. Pehle: {len(start)} issues, ab: {final} issues.")
    write_report(url, len(start), final, results)
    open("fixed_page.html", "w", encoding="utf-8").write(current)

def write_report(url, before_n, after_n, results):
    cards = ""
    for r in results:
        color = "#1a7f37" if r["ok"] else "#b42318"
        status = "Fixed" if r["ok"] else "Not fixed"
        cards += f"""<div class="card"><b>{H.escape(r['type'])}</b>
        <span style="color:{color}"> {status} (tries: {r['tries']})</span>
        <p>{H.escape(r['why'])}</p>
        <p>Before:</p><pre>{H.escape(r['before'][:600])}</pre>
        <p>After:</p><pre>{H.escape(r['after'][:600])}</pre></div>"""
    page = f"""<!doctype html><html lang="en"><meta charset="utf-8">
    <title>Accessibility Agent Report</title>
    <style>body{{font-family:Arial;max-width:900px;margin:30px auto;padding:0 16px}}
    .card{{border:1px solid #ccc;border-radius:8px;padding:12px;margin:12px 0}}
    pre{{background:#f4f4f4;padding:8px;overflow:auto;white-space:pre-wrap}}</style>
    <h1>Accessibility Agent Report</h1><p>URL: {H.escape(url)}</p>
    <h2>Issues: {before_n} before, {after_n} after</h2>{cards}</html>"""
    open("report.html", "w", encoding="utf-8").write(page)
    webbrowser.open("report.html")

if __name__ == "__main__":
    asyncio.run(run(sys.argv[1]))