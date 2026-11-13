"""Rewrite the publications table in README.md from the public ORCID API."""
import json
import re
import urllib.request

ORCID = "0009-0000-6335-6029"
# Optional extra links per DOI (lower-case DOI -> markdown).
EXTRA = {
    "10.1016/j.eswa.2025.127126": "[code](https://github.com/Tec4Tric/ESWA-NER-RE)",
    "10.1109/jcdl67857.2025.00039": "[code](https://github.com/Tec4Tric/ScholarScoreQA)",
    "10.1007/978-3-031-43458-7_11": "[dataset](https://github.com/Tec4Tric/AgriNER)",
}


def fetch():
    req = urllib.request.Request(
        f"https://pub.orcid.org/v3.0/{ORCID}/works",
        headers={"Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def rows(data):
    out = []
    for g in data.get("group", []):
        s = g["work-summary"][0]
        year = ((s.get("publication-date") or {}).get("year") or {}).get("value", "")
        title = s["title"]["title"]["value"].strip()
        venue = ((s.get("journal-title") or {}).get("value") or "").strip()
        doi = next(
            (e["external-id-value"] for e in g.get("external-ids", {}).get("external-id", [])
             if e["external-id-type"] == "doi"), "")
        links = [f"[DOI](https://doi.org/{doi})"] if doi else []
        if doi.lower() in EXTRA:
            links.append(EXTRA[doi.lower()])
        out.append((year, title, venue, " · ".join(links)))
    out.sort(key=lambda r: r[0], reverse=True)
    return out


def table(rs):
    lines = ["| Year | Title | Venue | Links |", "|---|---|---|---|"]
    for y, t, v, l in rs:
        lines.append(f"| {y} | {t.replace('|', '/')} | {v.replace('|', '/')} | {l} |")
    return "\n".join(lines)


def main():
    rs = rows(fetch())
    if not rs:
        raise SystemExit("ORCID returned no works; leaving README unchanged")
    text = open("README.md", encoding="utf-8").read()
    new = re.sub(
        r"(<!--PUBS:START-->).*?(<!--PUBS:END-->)",
        lambda m: f"{m.group(1)}\n{table(rs)}\n{m.group(2)}",
        text, flags=re.S)
    open("README.md", "w", encoding="utf-8", newline="\n").write(new)


if __name__ == "__main__":
    main()
