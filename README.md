# Just-Rice.github.io

The landing page at https://just-rice.github.io/: an index of my projects.
Plain HTML, no build tools to install. GitHub Pages serves `index.html` from `main`.

## How it works

- **`projects.json`** is the list. Each entry has a name, blurb, category (`games`, `learning`, `tools`),
  colour, tech tags, screenshot and dates. `"live": false` puts a project under "Also in the workshop".
  The big "Latest update" card at the top is whichever project was pushed to most recently;
  add `"pinned": true` to an entry to hold it there instead.
- **`scripts/build.py`** writes the cards into `index.html` between the `<!-- build:... -->` markers.
  Everything outside the markers is hand-written and left alone.
- **`scripts/sync.py`** checks my GitHub repos, refreshes each project's dates, and adds any new repo
  that has GitHub Pages switched on. It skips forks, archived repos, redirect-only repos and
  anything tagged `hide-from-home` or listed under `"skip"`.
- **`.github/workflows/sync.yml`** runs the sync every day (and on the Actions tab's "Run workflow"
  button), commits only if something changed, and the site updates itself.
- **`img/`** holds a 800×500 WebP screenshot per project, plus `og.png` for link previews.
  A project without a screenshot shows a coloured tile with its initial.

## Background and motion

Falling rice grains are drawn on a `<canvas>` behind the page and scatter from the pointer.
Cards rise in on load (each card's `--i` sets its place in the order), lean toward the mouse,
and glide to new places when a filter is used. Visitors with reduced motion switched on get a
still background and no animation. All of it is plain inline CSS and JavaScript in `index.html`.

## Adding a project by hand

1. Add an entry to `projects.json` (copy a neighbour).
2. Save a screenshot as `img/<repo>.webp`.
3. `python3 scripts/build.py`, check `index.html` in a browser, commit and push.

New Pages repos also appear on their own within a day; editing the auto-added entry
(`"auto_added": true`) afterwards to polish its blurb, colour and screenshot is expected.

GitHub repo topics steer the sync: `just-rice-home` lists a repo even without Pages,
`hide-from-home` keeps one off, `redirect` marks a forwarding-only repo.
