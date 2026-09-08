#!/usr/bin/env node
// render.mjs — turn a .mmd (Mermaid source) file into a self-contained local HTML
// page that renders it with the vendored mermaid.min.js and reports success/failure
// LOUDLY, both visually (a banner on the page) and programmatically
// (window.__harness, set on window so Playwright's browser_evaluate can read it).
//
// Zero npm dependencies — plain Node (fs/path/url only). This script only ever
// GENERATES html; actually rendering it requires a browser, which is why the
// harness hands off to the Playwright MCP tools (see README.md) rather than
// trying to drive a browser from here.
//
// Usage:
//   node render.mjs <input.mmd> <output.html> [diagramTitle]
//
// Why detection can't stop at "did mermaid throw": mermaid.render() does NOT
// throw on most syntax errors. Instead it resolves normally and produces an
// SVG containing a red "Syntax error in text" graphic. A screenshot of that
// looks like *a* diagram, so naive scripts that just check "did a screenshot
// get taken" will happily report a broken diagram as a pass. This harness
// specifically inspects the rendered SVG's text content and CSS classes for
// mermaid's own error markers, in addition to catching thrown exceptions and
// window.onerror / console.error.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const [, , mmdPath, outHtmlPath, titleArg] = process.argv;

if (!mmdPath || !outHtmlPath) {
  console.error("Usage: node render.mjs <input.mmd> <output.html> [title]");
  process.exit(2);
}

const mmdAbs = path.resolve(mmdPath);
if (!fs.existsSync(mmdAbs)) {
  console.error(`Input .mmd not found: ${mmdAbs}`);
  process.exit(2);
}

const source = fs.readFileSync(mmdAbs, "utf8");
const title = titleArg || path.basename(mmdAbs);

// The MCP Playwright browser has the file: protocol blocked, so the generated
// HTML must be served over http (see README: `python3 -m http.server`,
// rooted at or above experiments/agent-infra/). That means mermaid.min.js
// must be referenced by a *relative* URL that still resolves once both this
// output file and the harness folder are under the same served root — an
// absolute file:// src would silently fail to load under http.
const outAbs = path.resolve(outHtmlPath);
let mermaidUrl = path
  .relative(path.dirname(outAbs), path.join(__dirname, "mermaid.min.js"))
  .split(path.sep)
  .join("/");
if (!mermaidUrl.startsWith(".")) mermaidUrl = "./" + mermaidUrl;

// Embed the diagram source as a JSON string literal (not a raw <pre> block)
// so nothing about Mermaid's own syntax (quotes, backticks, `<br>`, literal
// "\n" sequences, etc.) can break out of the HTML/JS we generate around it.
const sourceJson = JSON.stringify(source);

const html = `<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>${escapeHtml(title)}</title>
<style>
  html, body { margin: 0; padding: 0; background: #ffffff; }
  body { font-family: -apple-system, Helvetica, Arial, sans-serif; padding: 24px; }
  #harness-status {
    position: fixed; top: 0; left: 0; right: 0; z-index: 9999;
    padding: 8px 12px; font-size: 13px; font-weight: 600;
    background: #444; color: #fff;
  }
  #harness-status.ok { background: #1a7f37; }
  #harness-status.fail { background: #c0272d; }
  #stage { margin-top: 40px; }
</style>
</head>
<body>
<div id="harness-status">RENDER: PENDING</div>
<div id="stage">
  <div class="mermaid" id="diagram-src">${escapeHtml(source)}</div>
</div>

<script src="${mermaidUrl}"></script>
<script>
(function () {
  // Structured result object — this is what browser_evaluate should read.
  window.__harness = {
    status: "pending",   // "ok" | "fail" | "pending"
    error: null,
    consoleErrors: [],
    source: ${sourceJson},
    done: false
  };

  var origError = console.error;
  console.error = function () {
    try {
      window.__harness.consoleErrors.push(Array.prototype.slice.call(arguments).map(String).join(" "));
    } catch (e) {}
    origError.apply(console, arguments);
  };

  window.addEventListener("error", function (ev) {
    window.__harness.status = "fail";
    window.__harness.error = "window.onerror: " + (ev && ev.message ? ev.message : String(ev));
    window.__harness.done = true;
    paintStatus();
  });

  function paintStatus() {
    var el = document.getElementById("harness-status");
    if (window.__harness.status === "ok") {
      el.textContent = "RENDER: OK";
      el.className = "ok";
    } else if (window.__harness.status === "fail") {
      el.textContent = "RENDER: FAIL — " + window.__harness.error;
      el.className = "fail";
    } else {
      el.textContent = "RENDER: PENDING";
      el.className = "";
    }
  }

  // Known signatures mermaid embeds into the SVG when it hits a parse error,
  // instead of throwing. This is the crux of the harness: a screenshot alone
  // cannot tell "here is a diagram" from "here is a diagram-shaped error".
  var ERROR_SIGNATURES = [
    "Syntax error in text",
    "mermaid version",
    "Parse error"
  ];

  function looksLikeMermaidErrorGraphic(svgEl) {
    if (!svgEl) return { hit: false };
    var text = svgEl.textContent || "";
    for (var i = 0; i < ERROR_SIGNATURES.length; i++) {
      if (text.indexOf(ERROR_SIGNATURES[i]) !== -1) {
        return { hit: true, reason: "SVG text contains \\"" + ERROR_SIGNATURES[i] + "\\"" };
      }
    }
    var errNode = svgEl.querySelector(".error-icon, .error-text, [id*='error'], [class*='error']");
    if (errNode) {
      return { hit: true, reason: "SVG contains an error-marked element (" + (errNode.getAttribute("class") || errNode.id) + ")" };
    }
    return { hit: false };
  }

  async function main() {
    try {
      mermaid.initialize({ startOnLoad: false, securityLevel: "loose" });
      var srcEl = document.getElementById("diagram-src");
      var src = window.__harness.source;
      var result = await mermaid.render("harness-rendered-svg", src);
      var svgMarkup = result.svg;
      srcEl.outerHTML = svgMarkup;

      var svgEl = document.querySelector("#stage svg");
      var check = looksLikeMermaidErrorGraphic(svgEl);
      if (check.hit) {
        window.__harness.status = "fail";
        window.__harness.error = "Mermaid rendered an inline error graphic (no exception thrown). " + check.reason;
      } else if (window.__harness.consoleErrors.length > 0) {
        window.__harness.status = "fail";
        window.__harness.error = "console.error was called during render: " + window.__harness.consoleErrors.join(" | ");
      } else {
        window.__harness.status = "ok";
      }
    } catch (e) {
      window.__harness.status = "fail";
      window.__harness.error = "exception: " + (e && e.message ? e.message : String(e));
    }
    window.__harness.done = true;
    paintStatus();
  }

  main();
})();
</script>
</body>
</html>
`;

fs.mkdirSync(path.dirname(path.resolve(outHtmlPath)), { recursive: true });
fs.writeFileSync(outHtmlPath, html, "utf8");
console.log(`Wrote ${outAbs}`);
console.log(
  `Serve it (file: is blocked in the MCP browser) e.g.:\n` +
    `  python3 -m http.server 8743 --directory experiments/agent-infra\n` +
    `then navigate Playwright MCP to the matching http://localhost:8743/... path.`
);

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}
