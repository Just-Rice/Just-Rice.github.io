#!/usr/bin/env python3
"""Write the project cards in index.html from projects.json.

Everything between <!-- build:NAME --> and <!-- /build:NAME --> in index.html is
regenerated; the rest of the page is left alone. Standard library only.

    python3 scripts/build.py
"""
import datetime as dt
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OWNER = "Just-Rice"
CATEGORIES = [("games", "Games"), ("learning", "Learning"), ("tools", "Tools & data")]


def esc(s):
    return html.escape(str(s), quote=True)


def live_url(p):
    return p.get("url") or f"https://just-rice.github.io/{p['repo']}/"


def repo_url(p):
    return f"https://github.com/{OWNER}/{p['repo']}"


def month(iso):
    if not iso:
        return ""
    return dt.date.fromisoformat(iso[:10]).strftime("%b %Y")


def picture(p, eager=False):
    name = esc(p["name"])
    if p.get("image") and (ROOT / p["image"]).exists():
        loading = 'fetchpriority="high"' if eager else 'loading="lazy"'
        return (f'<img src="{esc(p["image"])}" alt="Screenshot of {name}" '
                f'width="800" height="500" {loading} decoding="async">')
    # No screenshot yet: a coloured tile with the project's initial.
    return f'<span class="ph" aria-hidden="true">{esc(p["name"][:1].upper())}</span>'


def chips(p):
    return "".join(f"<li>{esc(s)}</li>" for s in p.get("stack", []))


def foot(p):
    updated = month(p.get("updated"))
    when = (f'<time datetime="{esc(p["updated"][:10])}">Updated {updated}</time>'
            if updated else "")
    return (f'<p class="foot"><span class="open">{esc(p.get("action", "Open"))} '
            f'<span class="arrow" aria-hidden="true">&rarr;</span></span>{when}'
            f'<a class="code" href="{repo_url(p)}">Code</a></p>')


def card(p):
    return f"""
      <article class="card" data-cat="{esc(p.get('category', 'tools'))}" style="--c:{esc(p.get('color', '#6B7480'))}">
        <div class="shot">{picture(p)}</div>
        <div class="body">
          <span class="kind">{esc(p.get('kind', 'Project'))}</span>
          <h3 class="title"><a href="{esc(live_url(p))}">{esc(p['name'])}</a></h3>
          <p>{esc(p.get('blurb', ''))}</p>
          <ul class="stack">{chips(p)}</ul>
          {foot(p)}
        </div>
      </article>"""


def featured(p):
    return f"""
    <article class="card feature" data-cat="{esc(p.get('category', 'tools'))}" style="--c:{esc(p.get('color', '#6B7480'))}">
      <div class="shot">{picture(p, eager=True)}</div>
      <div class="body">
        <span class="kind">Featured &middot; {esc(p.get('kind', 'Project'))}</span>
        <h3 class="title"><a href="{esc(live_url(p))}">{esc(p['name'])}</a></h3>
        <p>{esc(p.get('blurb', ''))}</p>
        <ul class="stack">{chips(p)}</ul>
        {foot(p)}
      </div>
    </article>"""


def workshop(p):
    return (f'\n      <a href="{repo_url(p)}"><strong>{esc(p["name"])}</strong>'
            f'<span>{esc(p.get("blurb", ""))}</span></a>')


def build():
    data = json.loads((ROOT / "projects.json").read_text())
    projects = data["projects"]
    live = [p for p in projects if p.get("live", True)]
    top = next((p for p in live if p.get("featured")), None)
    rest = sorted((p for p in live if p is not top),
                  key=lambda p: p.get("updated", ""), reverse=True)

    counts = {k: sum(p.get("category") == k for p in live) for k, _ in CATEGORIES}
    filters = [f'<button type="button" data-filter="all" aria-pressed="true">All <b>{len(live)}</b></button>']
    filters += [f'<button type="button" data-filter="{k}" aria-pressed="false">{esc(label)} <b>{counts[k]}</b></button>'
                for k, label in CATEGORIES if counts[k]]

    newest = max((p.get("updated", "") for p in projects), default="")
    parts = {
        "count": f"{len(live)} live projects",
        "featured": featured(top) + "\n    " if top else "",
        "filters": "\n      " + "\n      ".join(filters) + "\n      ",
        "grid": "".join(card(p) for p in rest) + "\n    ",
        "workshop": "".join(workshop(p) for p in projects if not p.get("live", True)) + "\n    ",
        "updated": (f'<time datetime="{esc(newest[:10])}">{dt.date.fromisoformat(newest[:10]).strftime("%-d %B %Y")}</time>'
                    if newest else ""),
    }

    page = (ROOT / "index.html").read_text()
    for name, content in parts.items():
        pattern = re.compile(rf"(<!-- build:{name} -->).*?(<!-- /build:{name} -->)", re.S)
        if not pattern.search(page):
            raise SystemExit(f"index.html is missing the build:{name} markers")
        page = pattern.sub(lambda m: m.group(1) + content + m.group(2), page)
    (ROOT / "index.html").write_text(page)
    print(f"Built index.html: {len(live)} live, {len(projects) - len(live)} in the workshop")


if __name__ == "__main__":
    build()
