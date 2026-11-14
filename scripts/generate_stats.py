"""Generate self-hosted GitHub stats cards (SVG) using the GitHub API.

Writes assets/stats.svg and assets/langs.svg. Needs GITHUB_TOKEN in the environment.
Only public data is used, so nothing about private repositories is exposed.
"""
import json
import os
import urllib.request
from html import escape

USER = os.environ.get("GH_USER", "Tec4Tric")
TOKEN = os.environ["GITHUB_TOKEN"]
HEAD = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json",
        "User-Agent": "profile-stats"}

ACCENT = "#2c9cdb"
TEXT = "#7d8590"
BORDER = "#8b949e"
FONT = "font-family=\"Segoe UI, Helvetica, Arial, sans-serif\""

LANG_COLORS = {"Python": "#3572A5", "Jupyter Notebook": "#DA5B0B", "HTML": "#e34c26", "C": "#555555",
               "JavaScript": "#f1e05a", "CSS": "#563d7c", "Shell": "#89e051", "TeX": "#3D6117"}


def get(url, data=None):
    req = urllib.request.Request(url, headers=HEAD, data=data)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def repos():
    out, page = [], 1
    while True:
        chunk = get(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner&page={page}")
        out += chunk
        if len(chunk) < 100:
            return out
        page += 1


def contributions():
    q = ('query($u:String!){user(login:$u){contributionsCollection{'
         'totalCommitContributions totalPullRequestContributions totalIssueContributions '
         'totalPullRequestReviewContributions}}}')
    body = json.dumps({"query": q, "variables": {"u": USER}}).encode()
    d = get("https://api.github.com/graphql", body)["data"]["user"]["contributionsCollection"]
    return sum(d.values()), d["totalCommitContributions"]


def card(width, height, title, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
            f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10" fill="none" stroke="{BORDER}" stroke-opacity=".35"/>'
            f'<text x="24" y="34" {FONT} font-size="17" font-weight="700" fill="{ACCENT}">{escape(title)}</text>{body}</svg>')


def main():
    u = get(f"https://api.github.com/users/{USER}")
    rs = [r for r in repos() if not r["private"]]
    own = [r for r in rs if not r["fork"]]
    stars = sum(r["stargazers_count"] for r in own)
    total, commits = contributions()

    rows = [("Public repositories", len(own)), ("Stars earned", stars),
            ("Contributions (last year)", total), ("Commits (last year)", commits),
            ("Followers", u["followers"])]
    body = ""
    for i, (k, v) in enumerate(rows):
        y = 66 + i * 26
        body += (f'<circle cx="30" cy="{y - 5}" r="4" fill="{ACCENT}"/>'
                 f'<text x="44" y="{y}" {FONT} font-size="14" fill="{TEXT}">{escape(k)}</text>'
                 f'<text x="330" y="{y}" {FONT} font-size="14" font-weight="700" fill="{ACCENT}" text-anchor="end">{v}</text>')
    open("assets/stats.svg", "w", encoding="utf-8").write(card(360, 200, f"{u.get('name') or USER}'s GitHub stats", body))

    langs = {}
    for r in own:
        for k, v in get(f"https://api.github.com/repos/{USER}/{r['name']}/languages").items():
            langs[k] = langs.get(k, 0) + v
    top = sorted(langs.items(), key=lambda kv: kv[1], reverse=True)[:6]
    tot = sum(langs.values()) or 1
    body = ""
    for i, (k, v) in enumerate(top):
        y = 70 + i * min(34, 130 // max(len(top), 1))
        pct = v / tot * 100
        color = LANG_COLORS.get(k, ACCENT)
        body += (f'<text x="24" y="{y}" {FONT} font-size="13" fill="{TEXT}">{escape(k)}</text>'
                 f'<rect x="150" y="{y - 10}" width="150" height="10" rx="5" fill="{BORDER}" fill-opacity=".2"/>'
                 f'<rect x="150" y="{y - 10}" width="{max(pct * 1.5, 3):.0f}" height="10" rx="5" fill="{color}"/>'
                 f'<text x="336" y="{y}" {FONT} font-size="12" fill="{TEXT}" text-anchor="end">{pct:.1f}%</text>')
    open("assets/langs.svg", "w", encoding="utf-8").write(card(360, 200, "Most used languages", body))


if __name__ == "__main__":
    main()
