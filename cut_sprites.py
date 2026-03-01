#!/usr/bin/env python3
"""
Taschen-Man Sprite Cutter
- Removes magenta/hot-pink background
- Auto-detects individual sprites via alpha gap scanning
- Saves to assets/ with clean names
- Generates sprite_review.html with original filenames, checkboxes, copy-skipped button
"""

import os, io, base64, math
from PIL import Image

DOWNLOADS = os.path.expanduser("~/Downloads")
HERE      = os.path.dirname(os.path.abspath(__file__))
ASSETS    = os.path.join(HERE, "assets")

S_CHAR, S_ITEM, S_HQ = 32, 16, 64

# Frames to skip: (asset_name, frame_index)
SKIP = {
    ("female_scared", 3),
    ("guard_scared",  1),
    ("guard_scared",  5),
}

# (original_filename, group, asset_name, label, target_px)
MANIFEST = [
    ("ChatGPT Image Feb 28, 2026, 02_33_34 PM.png",
     "player", "operative_walk_side",
     "Player — Covert Operative (side walk)", S_CHAR),

    ("ChatGPT Image Feb 28, 2026, 03_40_09 PM.png",
     "enemies", "ayatollah_normal",
     "Ayatollah — Normal", S_CHAR),

    ("scared_ayatolah.jpeg",
     "enemies", "ayatollah_scared",
     "Ayatollah — Scared (tears)", S_CHAR),

    ("ChatGPT Image Feb 28, 2026, 03_55_45 PM.png",
     "enemies", "guard_normal",
     "Revolutionary Guard — Normal", S_CHAR),

    ("ChatGPT Image Feb 28, 2026, 03_55_40 PM.png",
     "enemies", "guard_scared",
     "Revolutionary Guard — Scared (tears)", S_CHAR),

    ("ChatGPT Image Feb 28, 2026, 04_03_51 PM.png",
     "enemies", "basij_normal",
     "Basij Motorcycle — Normal", S_CHAR),

    ("ChatGPT Image Feb 28, 2026, 04_11_10 PM.png",
     "enemies", "basij_scared",
     "Basij Motorcycle — Scared (tears)", S_CHAR),

    ("ChatGPT Image Feb 28, 2026, 04_16_40 PM.png",
     "enemies", "female_normal",
     "Female Extremist — Normal", S_CHAR),

    ("ChatGPT Image Feb 28, 2026, 04_18_14 PM.png",
     "enemies", "female_scared",
     "Female Extremist — Scared (tears)", S_CHAR),

    ("ChatGPT Image Feb 28, 2026, 03_11_36 PM.png",
     "jet", "jet",
     "Fighter Jet — angles", S_CHAR),

    ("ChatGPT Image Feb 28, 2026, 02_57_13 PM.png",
     "trapdoor", "trapdoor_overhead",
     "Trap Door — Overhead view", S_CHAR),

    ("ChatGPT Image Feb 28, 2026, 02_57_25 PM.png",
     "trapdoor", "trapdoor_side",
     "Trap Door — Side view", S_CHAR),

    ("ChatGPT Image Feb 28, 2026, 05_15_36 PM.png",
     "buildings_a", "buildings_a",
     "Buildings Set A — 6 types", S_CHAR),

    ("ChatGPT Image Feb 28, 2026, 04_24_36 PM.png",
     "tiles", "street_tiles",
     "Street / Floor Tiles", S_CHAR),

    ("ChatGPT Image Feb 28, 2026, 05_24_25 PM.png",
     "hq", "compound",
     "Presidential Compound / Tehran HQ", S_HQ),

    ("ChatGPT Image Feb 28, 2026, 05_45_34 PM.png",
     "collectibles", "collectibles",
     "Collectibles — Mask×2  Scroll×2  Hamantaschen×2  Wine×2", S_ITEM),
]

# ── background removal ─────────────────────────────────────────────

def is_bg(r, g, b):
    """Hot-pink / magenta background. Uses colour distance for JPEG tolerance."""
    return math.sqrt((r - 255) ** 2 + g ** 2 + (b - 255) ** 2) < 95

def remove_bg(img):
    img = img.convert("RGBA")
    px  = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            if is_bg(r, g, b):
                px[x, y] = (0, 0, 0, 0)
    return img

# ── sprite detection ───────────────────────────────────────────────

def alpha_profile(img, axis):
    """Sum of alpha per column (axis=0) or row (axis=1)."""
    px = img.load()
    if axis == 0:
        return [sum(px[x, y][3] for y in range(img.height)) for x in range(img.width)]
    return [sum(px[x, y][3] for x in range(img.width)) for y in range(img.height)]

def find_spans(profile, min_gap=4):
    """
    Return (start, end) spans of non-zero regions.
    Gaps smaller than min_gap are bridged (handles tiny internal transparent bits).
    """
    on = [v > 0 for v in profile]

    # bridge small internal gaps
    i = 0
    while i < len(on):
        if not on[i]:
            j = i
            while j < len(on) and not on[j]:
                j += 1
            if j - i < min_gap:
                on[i:j] = [True] * (j - i)
            i = max(i + 1, j)
        else:
            i += 1

    spans, in_s, s0 = [], False, 0
    for i, v in enumerate(on):
        if v and not in_s:   s0 = i;  in_s = True
        elif not v and in_s: spans.append((s0, i)); in_s = False
    if in_s:
        spans.append((s0, len(on)))
    return spans

def cut_sprites(img, target_px):
    """Detect all sprites in sheet, resize each to target_px × target_px."""
    c_spans = find_spans(alpha_profile(img, 0))
    r_spans = find_spans(alpha_profile(img, 1))

    sprites = []
    for r0, r1 in r_spans:
        for c0, c1 in c_spans:
            crop = img.crop((c0, r0, c1, r1))
            px   = crop.load()
            w, h = crop.size
            filled = sum(1 for y in range(h) for x in range(w) if px[x, y][3] > 10)
            if filled / (w * h) > 0.04:          # skip near-empty crops
                sprites.append(crop.resize((target_px, target_px), Image.NEAREST))
    return sprites

# ── helpers ────────────────────────────────────────────────────────

def to_b64(img):
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()

# ── main processing ────────────────────────────────────────────────

def main():
    os.makedirs(ASSETS, exist_ok=True)

    all_groups = []
    global_n   = 1

    for src, group, name, label, target_px in MANIFEST:
        src_path = os.path.join(DOWNLOADS, src)
        if not os.path.exists(src_path):
            print(f"  ⚠  MISSING: {src}")
            continue

        print(f"  Processing: {label}")
        img     = Image.open(src_path)
        img     = remove_bg(img)
        sprites = cut_sprites(img, target_px)

        grp_dir = os.path.join(ASSETS, group)
        os.makedirs(grp_dir, exist_ok=True)

        frame_entries = []
        for i, sp in enumerate(sprites):
            if (name, i) in SKIP:
                continue
            fname = f"{name}_{i:02d}.png"
            sp.save(os.path.join(grp_dir, fname))
            frame_entries.append({
                "n":     global_n,
                "frame": i,
                "fname": fname,
                "path":  f"assets/{group}/{fname}",
                "src":   src,
                "label": label,
                "group": group,
                "b64":   to_b64(sp),
                "px":    target_px,
            })
            global_n += 1

        all_groups.append({
            "group":  group,
            "label":  label,
            "src":    src,
            "frames": frame_entries,
        })
        print(f"     → {len(sprites)} frames  →  assets/{group}/")

    generate_html(all_groups)
    print(f"\n✅  Done. Open sprite_review.html in your browser.")

# ── HTML generation ────────────────────────────────────────────────

def generate_html(groups):
    rows = []

    for g in groups:
        rows.append(f"""
  <tr class="grp-header">
    <td colspan="5">📁 {g['group'].upper()}</td>
  </tr>
  <tr class="grp-src">
    <td colspan="5">📄 <code>{g['src']}</code> &nbsp;—&nbsp; {g['label']}</td>
  </tr>""")

        for f in g['frames']:
            scale = max(2, 96 // f['px'])   # display ~96–128 px for visibility
            disp  = f['px'] * scale
            rows.append(f"""
  <tr class="frame-row" id="row-{f['n']}">
    <td class="num">#{f['n']}</td>
    <td class="img">
      <img src="data:image/png;base64,{f['b64']}"
           width="{disp}" height="{disp}"
           style="image-rendering:pixelated;background:#333;border-radius:4px">
    </td>
    <td class="desc">
      {f['label']}<br>
      <small>frame {f['frame']} &nbsp;·&nbsp; {f['px']}px &nbsp;·&nbsp;
             <code>{f['fname']}</code></small>
    </td>
    <td class="orig"><code>{f['src']}</code></td>
    <td class="use">
      <label>
        <input type="checkbox" checked data-n="{f['n']}"> USE
      </label>
    </td>
  </tr>""")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Taschen-Man — Sprite Review</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body  {{ background: #111; color: #ccc; font-family: 'Courier New', monospace; padding: 24px; }}
  h1    {{ color: #ffd700; font-size: 22px; margin-bottom: 6px; }}
  .sub  {{ color: #888; font-size: 12px; margin-bottom: 24px; }}

  table {{ border-collapse: collapse; width: 100%; }}
  td    {{ padding: 8px 12px; border-bottom: 1px solid #222; vertical-align: middle; }}

  .grp-header td {{
    background: #1e1200; color: #ffd700; font-size: 14px; font-weight: bold;
    padding: 14px 12px 4px; border-top: 2px solid #ffd700; letter-spacing: 1px;
  }}
  .grp-src td {{
    background: #161000; color: #666; font-size: 11px; padding: 3px 12px 12px;
  }}
  .grp-src code {{ color: #999; }}

  .frame-row:hover {{ background: #1a1a1a; }}
  .frame-row.off td {{ opacity: 0.25; }}
  .frame-row.off .use {{ opacity: 1; }}

  .num   {{ color: #555; font-size: 12px; width: 44px; }}
  .img   {{ width: 120px; }}
  .desc  {{ color: #ddd; font-size: 13px; line-height: 1.5; }}
  .desc small {{ color: #777; }}
  .desc code  {{ color: #88ff88; }}
  .orig  {{ font-size: 10px; color: #555; max-width: 280px; word-break: break-all; }}
  .orig code  {{ color: #667799; }}
  .use   {{ width: 70px; text-align: center; }}
  .use label  {{ cursor: pointer; color: #66aaff; font-size: 13px; }}
  .use input  {{ transform: scale(1.4); cursor: pointer; margin-right: 4px; }}

  #hud {{
    position: fixed; bottom: 20px; right: 20px;
    background: #1a1a1a; border: 1px solid #ffd700; border-radius: 8px;
    padding: 14px 18px; font-size: 13px; min-width: 180px;
  }}
  #hud h3   {{ color: #ffd700; font-size: 12px; margin-bottom: 8px; letter-spacing:1px; }}
  #hud .row {{ display: flex; justify-content: space-between; margin-bottom: 4px; }}
  #hud .row span {{ color: #fff; font-weight: bold; }}
  #copy-btn {{
    margin-top: 10px; width: 100%; padding: 7px 0;
    background: #ffd700; color: #111; border: none; border-radius: 4px;
    cursor: pointer; font-family: monospace; font-weight: bold; font-size: 12px;
  }}
  #copy-btn:hover {{ background: #ffe84d; }}
</style>
</head>
<body>

<h1>🎭 Taschen-Man — Sprite Review</h1>
<p class="sub">Uncheck any frames you don't want. Hit "Copy skipped #s" and paste to Claude.</p>

<table>
{''.join(rows)}
</table>

<div id="hud">
  <h3>SELECTION</h3>
  <div class="row">Using: <span id="cnt-on">0</span></div>
  <div class="row">Skipping: <span id="cnt-off">0</span></div>
  <button id="copy-btn" onclick="copySkipped()">📋 Copy skipped #s</button>
</div>

<script>
  const boxes   = document.querySelectorAll('input[type=checkbox]');
  const cntOn   = document.getElementById('cnt-on');
  const cntOff  = document.getElementById('cnt-off');

  function update() {{
    let on = 0, off = 0;
    boxes.forEach(b => {{
      const row = document.getElementById('row-' + b.dataset.n);
      if (b.checked) {{ on++;  row.classList.remove('off'); }}
      else           {{ off++; row.classList.add('off');    }}
    }});
    cntOn.textContent  = on;
    cntOff.textContent = off;
  }}

  boxes.forEach(b => b.addEventListener('change', update));
  update();

  function copySkipped() {{
    const skipped = [...boxes].filter(b => !b.checked).map(b => '#' + b.dataset.n);
    if (!skipped.length) {{ alert('Nothing skipped!'); return; }}
    navigator.clipboard.writeText('Skip: ' + skipped.join(', '));
    alert('Copied! (' + skipped.length + ' frames skipped)');
  }}
</script>
</body>
</html>"""

    out = os.path.join(HERE, "sprite_review.html")
    with open(out, "w") as f:
        f.write(html)
    print(f"  → sprite_review.html written")

if __name__ == "__main__":
    main()
