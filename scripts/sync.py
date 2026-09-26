#!/usr/bin/env python3
"""Bring projects.json up to date with the Just-Rice repos on GitHub, then rebuild.

- Refreshes each project's "added" and "updated" dates from GitHub.
- Adds any public repo that has GitHub Pages switched on (or the just-rice-home
  topic) and isn't listed yet, using its GitHub description, website and topics.
- Leaves out forks, archived repos, redirect-only repos (topic "redirect" or a
  description starting "Moved"/"Redirect"), repos with the topic hide-from-home,
  and anything named in projects.json's "skip" list.

    python3 scripts/sync.py            # update projects.json and index.html
    python3 scripts/sync.py --dry-run  # only report what would change

Set GITHUB_TOKEN to avoid the API's anonymous rate limit (the Action does this).
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402

ROOT = build.ROOT
OWNER = build.OWNER
PALETTE = ["#F2B01E", "#E2603A", "#D94F8A", "#2F8A5B", "#B4682A", "#7C5CD6",
           "#4E9B5B", "#2E7FE8", "#1C94A3", "#C2410C", "#0E7490", "#9D4EDD"]


def fetch_repos():
    req = urllib.request.Request(
        f"https://api.github.com/users/{OWNER}/repos?per_page=100&type=owner",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "just-rice-home-sync"})
    if os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def is_redirect(r):
    desc = (r.get("description") or "").lower()
    return "redirect" in r.get("topics", []) or desc.startswith(("moved", "redirect"))


def wanted(r):
    topics = r.get("topics", [])
    return (not r["fork"] and not r["archived"] and not r["private"]
            and (r.get("has_pages") or "just-rice-home" in topics)
            and "hide-from-home" not in topics and not is_redirect(r))


def guess_category(topics):
    t = set(topics)
    if t & {"game", "games", "browser-game", "board-game"}:
        return "games", "Game", "Play"
    if t & {"education", "study-tool", "explainer", "learning"}:
        return "learning", "Study tool", "Open"
    return "tools", "Tool", "Open"


def new_entry(r, used_colors):
    cat, kind, action = guess_category(r.get("topics", []))
    color = next((c for c in PALETTE if c not in used_colors), PALETTE[len(used_colors) % len(PALETTE)])
    home = r.get("homepage") or ""
    entry = {
        "repo": r["name"],
        "name": r["name"].replace("-", " ").title() if r["name"].islower() else r["name"],
        "kind": kind,
        "category": cat,
        "color": color,
        "blurb": r.get("description") or "A new project.",
        "stack": [r["language"]] if r.get("language") else [],
        "action": action,
        "image": f"img/{r['name'].lower()}.webp",
        "live": True,
        "auto_added": True,
    }
    if home.startswith("https://just-rice.github.io/") and home.rstrip("/") != f"https://just-rice.github.io/{r['name']}":
        entry["url"] = home
    return entry


def sync(dry_run=False):
    path = ROOT / "projects.json"
    data = json.loads(path.read_text())
    projects = data["projects"]
    skip = {s.lower() for s in data.get("skip", [])}
    repos = {r["name"].lower(): r for r in fetch_repos()}
    changes = []

    for p in projects:
        r = repos.get(p["repo"].lower())
        if not r:
            changes.append(f"warning: {p['repo']} is not a public repo any more (left as is)")
            continue
        for key, value in (("added", r["created_at"][:10]), ("updated", r["pushed_at"][:10])):
            if p.get(key) != value:
                changes.append(f"{p['repo']}: {key} {p.get(key)} -> {value}")
                p[key] = value

    listed = {p["repo"].lower() for p in projects}
    used = {p.get("color") for p in projects}
    for name, r in sorted(repos.items(), key=lambda kv: kv[1]["created_at"]):
        if name in listed or name in skip or not wanted(r):
            continue
        entry = new_entry(r, used)
        entry["added"], entry["updated"] = r["created_at"][:10], r["pushed_at"][:10]
        used.add(entry["color"])
        projects.append(entry)
        changes.append(f"added new project: {r['name']}")

    print("\n".join(changes) or "No changes: projects.json already matches GitHub.")
    if dry_run or not any(not c.startswith("warning") for c in changes):
        return
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    build.build()


if __name__ == "__main__":
    sync(dry_run="--dry-run" in sys.argv)
