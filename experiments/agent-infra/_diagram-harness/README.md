# Diagram render/verify harness

This is the shared tool used across `experiments/agent-infra/*/` to satisfy
step 3 of `planning/PLAN.md`'s working method: every Mermaid diagram must be
**rendered and visually confirmed** before the concept prose that depends on
it gets written. It exists because Mermaid does not fail loudly by default —
see "Why a green screenshot is not proof" below.

## What's here

- `mermaid.min.js` — mermaid v11, vendored from
  `https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js` so rendering
  is offline/reproducible and nothing is added to this repo's dependencies.
- `render.mjs` — a zero-dependency Node script. Given a `.mmd` file, it
  generates a self-contained HTML page that loads the vendored mermaid build,
  renders the diagram, and exposes a structured `window.__harness` result
  plus a big visual status banner.
- `fixtures/` — a known-good and a **known-broken** diagram, with their
  rendered HTML/PNG committed as proof the harness actually distinguishes
  the two (see "Self-test" below). Keep this fixture — a verifier that has
  never been shown to fail is not trustworthy.

## How to run it on one `.mmd`

```bash
# 1. Generate the render page next to (or wherever) you like — the script
#    always references the vendored mermaid.min.js by a relative path.
node experiments/agent-infra/_diagram-harness/render.mjs \
  experiments/agent-infra/state/diagram.mmd \
  experiments/agent-infra/state/_render.html

# 2. Serve it. The Playwright MCP browser used in this session has the
#    file: protocol BLOCKED, so you cannot just browser_navigate to a
#    file:// URL — it errors with "Access to file: protocol is blocked".
#    Serve the folder over plain HTTP instead (any static server works;
#    python3 is always available here):
python3 -m http.server 8743 --directory experiments/agent-infra
```

Then, with the Playwright MCP tools:

3. `browser_navigate` to `http://127.0.0.1:8743/state/_render.html` (path is
   relative to whatever directory you passed to `--directory`).
4. `browser_evaluate` with a function that polls until done, e.g.:
   ```js
   async () => {
     for (let i = 0; i < 50; i++) {
       if (window.__harness && window.__harness.done) return window.__harness;
       await new Promise(r => setTimeout(r, 100));
     }
     return { ...window.__harness, timedOut: true };
   }
   ```
   Check `result.status === "ok"` and `result.error === null`. Also confirm
   the page URL in the tool's own response actually matches the file you
   navigated to (see "Shared browser" warning below) before trusting the
   result.
5. `browser_console_messages` (level `error`) as a second check — the page
   also funnels `console.error` calls into `window.__harness.consoleErrors`,
   but checking the browser's own console is a good independent cross-check.
6. `browser_take_screenshot` to save the PNG. Do this **after** step 4/5 so
   you know what you're capturing is the finished, evaluated state, not a
   half-rendered page.
7. Look at the screenshot yourself and compare it to what the experiment's
   `NOTES.md`/`RUN.md` claims — the harness catches "this doesn't parse", not
   "this diagram says something false about the experiment." That second
   check is a human/agent visual-inspection step, not something `render.mjs`
   can automate.

## Why a green screenshot is not proof

Mermaid does not throw a normal JS exception for most syntax problems.
`mermaid.render()` can resolve "successfully" while the SVG it hands back is
just mermaid's own error graphic — a bomb icon and the text "Syntax error in
text". A script that only checks "did a screenshot get taken without the
page crashing" will happily report a broken diagram as a pass.

`render.mjs` guards against this two ways:
1. It wraps the render call in try/catch — `mermaid.render()` frequently
   *does* reject on parse errors (see `fixtures/known-broken.*`), and the
   thrown message is captured into `window.__harness.error`.
2. Independently of (1), it inspects the resulting SVG's text content and
   element classes for mermaid's own error signatures ("Syntax error in
   text", `.error-icon`, etc.) — this is the path that catches errors
   mermaid swallows instead of throwing.

Either path sets `window.__harness.status = "fail"` and repaints the on-page
banner red with the specific error message, so failure is loud in both the
structured result *and* the screenshot itself.

## Self-test (why you can trust this)

`fixtures/known-good.mmd` (a 3-node flowchart) and `fixtures/known-broken.mmd`
(deliberately malformed) were both run through the full procedure above.
Committed results:

| fixture | `window.__harness.status` | banner in screenshot |
|---|---|---|
| `known-good.html` / `.png` | `"ok"` | green "RENDER: OK" |
| `known-broken.html` / `.png` | `"fail"` | red "RENDER: FAIL — exception: Parse error on line 2: ..." plus mermaid's own bomb-icon error graphic |

In this case mermaid actually threw on the broken fixture (caught by path 1
above); the SVG-inspection fallback (path 2) exists for the cases — noted in
the task that produced this harness — where mermaid resolves without
throwing but still emits an inline error graphic. A verifier that cannot be
shown to fail is not proof of anything, which is why this fixture pair is
committed rather than thrown away after use.

## Known limitation: the Playwright MCP browser is shared

The `browser_navigate` / `browser_evaluate` / `browser_take_screenshot` MCP
tools in this session drive **one shared browser instance** — if another
agent in the team navigates it between your `browser_navigate` and your next
tool call, your next call can silently run against *their* page. Always
check the `Page URL:` line in each MCP tool's own response against the URL
you expect before trusting `browser_evaluate`/`browser_take_screenshot`
output. If it doesn't match, re-navigate and retry.

## Why no scripted (non-MCP) batch runner

The task allows "a scripted node/playwright approach ... for batch work" as
an alternative, but actually running Playwright's Node API requires
`require("playwright")`, which in turn requires installing the `playwright`
npm package somewhere `node`'s module resolution can see it — that means a
`node_modules/` inside this repo, which is exactly what we were told not to
add. (`npx -p playwright node script.js` does *not* expose the package to a
plain `require()` — confirmed by testing — so there is no way to get the
Node API from npx's cache alone.) The Playwright MCP tools already available
to this agent don't have that problem, so they're the only approach used
here.
