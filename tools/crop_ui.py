#!/usr/bin/env python3
"""Monthly-recap crop UI — a tiny local web app for cropping each photo.

This is NOT part of the ad pipeline. It supports the monthly "tattoos I worked
on this month" recap: you drop a month's photos in a folder, open this UI, draw
an aspect-locked crop box on each one, and it writes a `crops.json` that
`build_recap.py` turns into the fast-cut montage video.

Standard library only (http.server). No Pillow, no ffprobe: the browser reads
each photo's real pixel size, and crops are stored as FRACTIONS (0..1) of the
source image, so they apply at any resolution.

  uv run tools/crop_ui.py work/monthly-recap/2026-11
  uv run tools/crop_ui.py work/monthly-recap/2026-11 --aspect 1:1 --port 8800

Layout it expects / creates:
  <folder>/photos/      <- you drop this month's photos here (jpg/png/webp)
  <folder>/crops.json   <- written when you Save

Then:
  uv run tools/build_recap.py work/monthly-recap/2026-11
"""

from __future__ import annotations

import argparse
import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
MIME = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".bmp": "image/bmp",
}


def list_photos(photos_dir: Path) -> list[str]:
    if not photos_dir.is_dir():
        return []
    names = [p.name for p in photos_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
    return sorted(names, key=str.lower)


def load_crops(crops_path: Path) -> dict:
    if crops_path.is_file():
        try:
            return json.loads(crops_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    return {}


def build_state(photos_dir: Path, crops_path: Path, aspect: str, target: tuple[int, int]) -> dict:
    """Merge the photos on disk with any saved crops, preserving saved order."""
    saved = load_crops(crops_path)
    saved_items = {item["file"]: item for item in saved.get("photos", []) if "file" in item}
    on_disk = list_photos(photos_dir)

    photos: list[dict] = []
    # Keep saved order first (for files that still exist), then append new files.
    for item in saved.get("photos", []):
        name = item.get("file")
        if name in on_disk and name not in {p["file"] for p in photos}:
            photos.append({
                "file": name,
                "crop": item.get("crop"),  # may be None -> UI picks a default
                "include": item.get("include", True),
            })
    for name in on_disk:
        if name not in {p["file"] for p in photos}:
            photos.append({"file": name, "crop": None, "include": True})

    return {
        "aspect": aspect,
        "target_w": target[0],
        "target_h": target[1],
        "photos": photos,
        "folder": str(photos_dir.parent),
    }


def make_handler(photos_dir: Path, crops_path: Path, aspect: str, target: tuple[int, int]):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # quiet
            pass

        def _send(self, code: int, body: bytes, content_type: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, obj) -> None:
            self._send(200, json.dumps(obj).encode("utf-8"), "application/json")

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/":
                self._send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")
                return
            if path == "/api/state":
                self._send_json(build_state(photos_dir, crops_path, aspect, target))
                return
            if path.startswith("/img/"):
                name = unquote(path[len("/img/"):])
                target_file = (photos_dir / name).resolve()
                # Path-traversal guard: must live directly in photos_dir.
                if target_file.parent != photos_dir.resolve() or not target_file.is_file():
                    self._send(404, b"not found", "text/plain")
                    return
                ctype = MIME.get(target_file.suffix.lower(), "application/octet-stream")
                self._send(200, target_file.read_bytes(), ctype)
                return
            self._send(404, b"not found", "text/plain")

        def do_POST(self):
            path = urlparse(self.path).path
            if path != "/api/save":
                self._send(404, b"not found", "text/plain")
                return
            length = int(self.headers.get("Content-Length", "0"))
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except (ValueError, json.JSONDecodeError):
                self._send(400, b"bad json", "text/plain")
                return
            out = {
                "aspect": aspect,
                "target_w": target[0],
                "target_h": target[1],
                "photos": payload.get("photos", []),
            }
            crops_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
            self._send_json({"ok": True, "saved": str(crops_path), "count": len(out["photos"])})

    return Handler


PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Recap crop</title>
<style>
  :root {
    --bg: #15161a; --panel: #1e2027; --line: #2d303a; --ink: #e8eaf0;
    --muted: #9aa0ad; --accent: #4f8cff; --accent-ink: #fff; --warn: #ff6b6b;
    --ok: #3fd07f;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; background: var(--bg); color: var(--ink);
    font: 14px/1.4 -apple-system, Segoe UI, Roboto, sans-serif;
    height: 100vh; display: flex; flex-direction: column; overflow: hidden;
  }
  header {
    display: flex; align-items: center; gap: 16px; padding: 10px 16px;
    border-bottom: 1px solid var(--line); background: var(--panel);
  }
  header h1 { font-size: 14px; margin: 0; font-weight: 600; }
  header .path { color: var(--muted); font-size: 12px; }
  header .spacer { flex: 1; }
  .status { font-size: 12px; color: var(--muted); }
  .status.dirty { color: var(--warn); }
  .status.saved { color: var(--ok); }
  button {
    background: var(--panel); color: var(--ink); border: 1px solid var(--line);
    border-radius: 7px; padding: 7px 12px; cursor: pointer; font-size: 13px;
  }
  button:hover { border-color: var(--accent); }
  button.primary { background: var(--accent); border-color: var(--accent); color: var(--accent-ink); }
  button:disabled { opacity: .4; cursor: default; }
  main { flex: 1; display: flex; min-height: 0; }
  #strip {
    width: 150px; flex-shrink: 0; overflow-y: auto; border-right: 1px solid var(--line);
    background: var(--panel); padding: 8px;
  }
  .thumb {
    position: relative; margin-bottom: 8px; border: 2px solid transparent;
    border-radius: 6px; overflow: hidden; cursor: pointer; background: #000;
  }
  .thumb.active { border-color: var(--accent); }
  .thumb.excluded { opacity: .35; }
  .thumb img { width: 100%; display: block; aspect-ratio: 1; object-fit: cover; }
  .thumb .idx {
    position: absolute; top: 3px; left: 3px; background: rgba(0,0,0,.65);
    color: #fff; font-size: 11px; padding: 1px 6px; border-radius: 10px;
  }
  .thumb .name {
    position: absolute; bottom: 0; left: 0; right: 0; font-size: 10px;
    padding: 2px 4px; background: rgba(0,0,0,.6); white-space: nowrap;
    overflow: hidden; text-overflow: ellipsis;
  }
  .thumb .reorder {
    position: absolute; top: 3px; right: 3px; display: flex; gap: 2px; opacity: 0;
  }
  .thumb:hover .reorder { opacity: 1; }
  .thumb .reorder button { padding: 0 5px; font-size: 11px; line-height: 18px; }
  #stage {
    flex: 1; display: flex; flex-direction: column; align-items: center;
    justify-content: center; padding: 16px; min-width: 0; position: relative;
  }
  #canvas-wrap { position: relative; max-width: 100%; max-height: 100%; }
  #photo { display: block; max-width: 100%; max-height: calc(100vh - 160px);
           user-select: none; -webkit-user-drag: none; }
  #overlay { position: absolute; inset: 0; }
  .shade { position: absolute; background: rgba(10,11,14,.68); pointer-events: none; }
  #cropbox {
    position: absolute; border: 2px solid var(--accent);
    box-shadow: 0 0 0 1px rgba(0,0,0,.5); cursor: move;
  }
  .handle {
    position: absolute; width: 16px; height: 16px; background: var(--accent);
    border: 2px solid #fff; border-radius: 50%;
  }
  .handle.nw { left: -9px; top: -9px; cursor: nwse-resize; }
  .handle.ne { right: -9px; top: -9px; cursor: nesw-resize; }
  .handle.sw { left: -9px; bottom: -9px; cursor: nesw-resize; }
  .handle.se { right: -9px; bottom: -9px; cursor: nwse-resize; }
  #toolbar { display: flex; gap: 8px; align-items: center; margin-top: 12px; }
  .empty { color: var(--muted); text-align: center; max-width: 440px; }
  .empty code { background: var(--panel); padding: 2px 6px; border-radius: 4px; }
  kbd { background: var(--panel); border: 1px solid var(--line); border-bottom-width: 2px;
        border-radius: 4px; padding: 1px 6px; font-size: 11px; }
</style>
</head>
<body>
<header>
  <h1>Recap crop</h1>
  <span class="path" id="folder"></span>
  <span class="path" id="aspect"></span>
  <span class="spacer"></span>
  <span class="status" id="status">loading…</span>
  <button id="reset">Reset crop</button>
  <button id="save" class="primary">Save crops.json</button>
</header>
<main>
  <div id="strip"></div>
  <div id="stage">
    <div id="canvas-wrap">
      <img id="photo" alt="">
      <div id="overlay">
        <div class="shade" id="shade-top"></div>
        <div class="shade" id="shade-bottom"></div>
        <div class="shade" id="shade-left"></div>
        <div class="shade" id="shade-right"></div>
        <div id="cropbox">
          <div class="handle nw" data-h="nw"></div>
          <div class="handle ne" data-h="ne"></div>
          <div class="handle sw" data-h="sw"></div>
          <div class="handle se" data-h="se"></div>
        </div>
      </div>
    </div>
    <div class="empty" id="empty" style="display:none"></div>
    <div id="toolbar">
      <button id="prev">&larr; Prev</button>
      <span id="counter" class="status"></span>
      <button id="next">Next &rarr;</button>
      <button id="toggle">Exclude from video</button>
    </div>
  </div>
</main>
<script>
"use strict";
let STATE = null;          // {aspect, target_w, target_h, photos:[{file,crop,include}]}
let R = 9 / 16;           // crop width / height
let cur = 0;
let dirty = false;
let natural = { w: 0, h: 0 };   // natural pixels of the loaded image
let rect = { w: 0, h: 0, left: 0, top: 0 };  // displayed image box in px (within wrap)

const $ = (id) => document.getElementById(id);
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

async function load() {
  const r = await fetch("/api/state");
  STATE = await r.json();
  const [aw, ah] = STATE.aspect.split(":").map(Number);
  R = aw / ah;
  $("folder").textContent = STATE.folder;
  $("aspect").textContent = "· " + STATE.aspect + " (" + STATE.target_w + "×" + STATE.target_h + ")";
  if (!STATE.photos.length) {
    $("canvas-wrap").style.display = "none";
    $("toolbar").style.display = "none";
    $("save").disabled = true; $("reset").disabled = true;
    const e = $("empty"); e.style.display = "block";
    e.innerHTML = "No photos found in <code>" + STATE.folder +
      "\\photos</code>.<br>Drop this month's photos there and reload.";
    setStatus("no photos", "");
    return;
  }
  renderStrip();
  select(0);
  setStatus("ready", "saved");
}

function setStatus(text, cls) {
  const s = $("status"); s.textContent = text; s.className = "status " + (cls || "");
}
function markDirty() { dirty = true; setStatus("unsaved changes", "dirty"); }

function renderStrip() {
  const strip = $("strip");
  strip.innerHTML = "";
  STATE.photos.forEach((p, i) => {
    const d = document.createElement("div");
    d.className = "thumb" + (i === cur ? " active" : "") + (p.include ? "" : " excluded");
    d.onclick = (ev) => { if (!ev.target.closest(".reorder")) select(i); };
    d.innerHTML =
      '<img src="/img/' + encodeURIComponent(p.file) + '" loading="lazy">' +
      '<span class="idx">' + (i + 1) + '</span>' +
      '<span class="name">' + p.file + '</span>' +
      '<span class="reorder"><button data-up>▲</button><button data-dn>▼</button></span>';
    d.querySelector("[data-up]").onclick = (e) => { e.stopPropagation(); move(i, -1); };
    d.querySelector("[data-dn]").onclick = (e) => { e.stopPropagation(); move(i, 1); };
    strip.appendChild(d);
  });
}

function move(i, dir) {
  const j = i + dir;
  if (j < 0 || j >= STATE.photos.length) return;
  const arr = STATE.photos;
  [arr[i], arr[j]] = [arr[j], arr[i]];
  if (cur === i) cur = j; else if (cur === j) cur = i;
  markDirty(); renderStrip(); refreshCounter();
}

function select(i) {
  cur = i;
  const p = STATE.photos[i];
  const img = $("photo");
  img.onload = () => {
    natural = { w: img.naturalWidth, h: img.naturalHeight };
    measure();
    if (!p.crop) p.crop = defaultCrop();
    drawCrop();
  };
  img.src = "/img/" + encodeURIComponent(p.file);
  renderStrip();
  refreshCounter();
  updateToggle();
}

function refreshCounter() {
  $("counter").textContent = (cur + 1) + " / " + STATE.photos.length;
}
function updateToggle() {
  $("toggle").textContent = STATE.photos[cur].include ? "Exclude from video" : "Include in video";
}

// Measure where the <img> content box actually sits inside the wrap.
function measure() {
  const img = $("photo");
  const wrap = $("canvas-wrap");
  const ib = img.getBoundingClientRect();
  const wb = wrap.getBoundingClientRect();
  rect = { w: ib.width, h: ib.height, left: ib.left - wb.left, top: ib.top - wb.top };
  $("overlay").style.left = rect.left + "px";
  $("overlay").style.top = rect.top + "px";
  $("overlay").style.width = rect.w + "px";
  $("overlay").style.height = rect.h + "px";
}

// Largest centered box of aspect R, in fractions of the source image.
function defaultCrop() {
  const imgR = natural.w / natural.h;
  let w, h;
  if (imgR > R) { h = 1; w = (R / imgR); }      // image wider than target -> limit width
  else { w = 1; h = (imgR / R); }               // image taller -> limit height
  return { x: (1 - w) / 2, y: (1 - h) / 2, w, h };
}

// Convert current crop fractions -> pixel box inside overlay, draw it + shades.
function drawCrop() {
  const c = STATE.photos[cur].crop;
  const box = $("cropbox");
  const L = c.x * rect.w, T = c.y * rect.h, W = c.w * rect.w, H = c.h * rect.h;
  box.style.left = L + "px"; box.style.top = T + "px";
  box.style.width = W + "px"; box.style.height = H + "px";
  $("shade-top").style.cssText = `left:0;top:0;width:100%;height:${T}px`;
  $("shade-bottom").style.cssText = `left:0;top:${T + H}px;width:100%;height:${rect.h - T - H}px`;
  $("shade-left").style.cssText = `left:0;top:${T}px;width:${L}px;height:${H}px`;
  $("shade-right").style.cssText = `left:${L + W}px;top:${T}px;width:${rect.w - L - W}px;height:${H}px`;
}

// ---- drag + resize (work in overlay px, keep aspect = R, clamp to [0, rect]) ----
let drag = null;
function pxCrop() {
  const c = STATE.photos[cur].crop;
  return { L: c.x * rect.w, T: c.y * rect.h, W: c.w * rect.w, H: c.h * rect.h };
}
function commitPx(L, T, W, H) {
  STATE.photos[cur].crop = { x: L / rect.w, y: T / rect.h, w: W / rect.w, h: H / rect.h };
  drawCrop();
}

$("cropbox").addEventListener("pointerdown", (e) => {
  const handle = e.target.dataset.h;
  const p = pxCrop();
  drag = { handle, startX: e.clientX, startY: e.clientY, ...p };
  e.target.setPointerCapture(e.pointerId);
  e.preventDefault();
});
window.addEventListener("pointermove", (e) => {
  if (!drag) return;
  const dx = e.clientX - drag.startX, dy = e.clientY - drag.startY;
  // rect.w / rect.h are the displayed image box; R is width/height in px too.
  const boxR = R; // displayed px aspect equals source aspect (uniform scale)
  if (!drag.handle) {
    // move
    let L = clamp(drag.L + dx, 0, rect.w - drag.W);
    let T = clamp(drag.T + dy, 0, rect.h - drag.H);
    commitPx(L, T, drag.W, drag.H);
    return;
  }
  // resize from a corner, keeping the opposite corner fixed and aspect locked.
  const right = drag.L + drag.W, bottom = drag.T + drag.H;
  let W, H, L, T;
  if (drag.handle === "se") {
    W = clamp(drag.W + dx, 20, rect.w - drag.L); H = W / boxR;
    if (drag.T + H > rect.h) { H = rect.h - drag.T; W = H * boxR; }
    L = drag.L; T = drag.T;
  } else if (drag.handle === "sw") {
    W = clamp(drag.W - dx, 20, right); H = W / boxR;
    if (drag.T + H > rect.h) { H = rect.h - drag.T; W = H * boxR; }
    L = right - W; T = drag.T;
  } else if (drag.handle === "ne") {
    W = clamp(drag.W + dx, 20, rect.w - drag.L); H = W / boxR;
    if (bottom - H < 0) { H = bottom; W = H * boxR; }
    L = drag.L; T = bottom - H;
  } else { // nw
    W = clamp(drag.W - dx, 20, right); H = W / boxR;
    if (bottom - H < 0) { H = bottom; W = H * boxR; }
    L = right - W; T = bottom - H;
  }
  commitPx(L, T, W, H);
});
window.addEventListener("pointerup", () => { if (drag) { drag = null; markDirty(); } });

// ---- controls ----
$("prev").onclick = () => select((cur - 1 + STATE.photos.length) % STATE.photos.length);
$("next").onclick = () => select((cur + 1) % STATE.photos.length);
$("reset").onclick = () => { STATE.photos[cur].crop = defaultCrop(); drawCrop(); markDirty(); };
$("toggle").onclick = () => {
  STATE.photos[cur].include = !STATE.photos[cur].include;
  updateToggle(); renderStrip(); markDirty();
};
$("save").onclick = save;
window.addEventListener("keydown", (e) => {
  if (e.target.tagName === "INPUT") return;
  if (e.key === "ArrowLeft") $("prev").click();
  else if (e.key === "ArrowRight") $("next").click();
  else if ((e.key === "s") && (e.metaKey || e.ctrlKey)) { e.preventDefault(); save(); }
});
window.addEventListener("resize", () => { if (STATE && STATE.photos.length) { measure(); drawCrop(); } });
window.addEventListener("beforeunload", (e) => { if (dirty) { e.preventDefault(); e.returnValue = ""; } });

async function save() {
  setStatus("saving…", "");
  const body = JSON.stringify({ photos: STATE.photos });
  const r = await fetch("/api/save", { method: "POST", headers: { "Content-Type": "application/json" }, body });
  const j = await r.json();
  if (j.ok) { dirty = false; setStatus("saved " + j.count + " photos → crops.json", "saved"); }
  else setStatus("save failed", "dirty");
}

load();
</script>
</body>
</html>
"""


def main() -> None:
    p = argparse.ArgumentParser(description="Local crop UI for the monthly recap video.")
    p.add_argument("folder", help="Month folder, e.g. work/monthly-recap/2026-11 (photos live in <folder>/photos).")
    p.add_argument("--aspect", default="9:16", help="Crop aspect ratio (default 9:16 for Reels/Stories).")
    p.add_argument("--port", type=int, default=8765, help="Local port (default 8765).")
    p.add_argument("--no-open", action="store_true", help="Do not auto-open a browser.")
    args = p.parse_args()

    folder = Path(args.folder).resolve()
    photos_dir = folder / "photos"
    crops_path = folder / "crops.json"
    photos_dir.mkdir(parents=True, exist_ok=True)

    try:
        w, h = (int(x) for x in args.aspect.split(":"))
    except ValueError:
        raise SystemExit(f"--aspect must look like 9:16, got {args.aspect!r}")

    count = len(list_photos(photos_dir))
    handler = make_handler(photos_dir, crops_path, args.aspect, (w, h))
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    url = f"http://127.0.0.1:{args.port}/"

    print(f"Crop UI for {folder}")
    print(f"  photos: {photos_dir}  ({count} image{'s' if count != 1 else ''})")
    print(f"  saves:  {crops_path}")
    print(f"  open:   {url}")
    if count == 0:
        print("  NOTE: no photos yet — drop images in the photos folder and reload the page.")
    print("Press Ctrl+C to stop.")

    if not args.no_open:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.shutdown()


if __name__ == "__main__":
    main()
