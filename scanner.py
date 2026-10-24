import requests
from bs4 import BeautifulSoup

def scan(html):
    soup = BeautifulSoup(html, "html.parser")
    issues = []

    for img in soup.find_all("img"):
        if img.get("alt") is None:
            issues.append({"type": "image-alt", "html": str(img)})

    for el in soup.find_all(["button", "a"]):
        if el.get_text(strip=True) or el.get("aria-label") or el.get("title"):
            continue
        inner = el.find("img", alt=True)
        if inner and inner.get("alt", "").strip():
            continue
        if el.name == "a" and not el.get("href"):
            continue
        kind = "button-name" if el.name == "button" else "link-name"
        issues.append({"type": kind, "html": str(el)})

    for inp in soup.find_all(["input", "textarea", "select"]):
        if inp.get("type") in ("hidden", "submit", "button", "image", "reset"):
            continue
        if inp.get("aria-label") or inp.get("aria-labelledby"):
            continue
        id_ = inp.get("id")
        if id_ and soup.find("label", attrs={"for": id_}):
            continue
        if inp.find_parent("label"):
            continue
        issues.append({"type": "input-label", "html": str(inp)})

    tag = soup.find("html")
    if tag and not tag.get("lang"):
        issues.append({"type": "html-lang", "html": "<html>"})

    return issues

def fetch(url):
    r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    return r.text

if __name__ == "__main__":
    import sys
    issues = scan(fetch(sys.argv[1]))
    print(len(issues), "issues mile")
    for i in issues:
        print("-", i["type"], "|", i["html"][:150])