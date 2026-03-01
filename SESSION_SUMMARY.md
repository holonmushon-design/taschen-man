# Taschen-Man — Session Summary (Feb 28, 2026)

## What Was Done This Session

### Sprites & Assets
- Processed `palace.png` (ChatGPT pixel art, magenta bg) → `assets/hq/compound_00.png` (384×256, cropped to content bounds)
- All sprites wired into game via `SPRITE_DEFS` loader
- Added `tiles` (street tiles) and `compound` (palace) to loader
- Fixed: player sprites flip for LEFT (face RIGHT natively)
- Fixed: enemy sprites flip for RIGHT (face LEFT natively)
- Fixed: ayatollah side sprites use correct flip per direction

### Rendering
- Street tiles drawn on all path cells (5 grayish tiles, excluded near-white tile_03)
- Buildings drawn at CELL×CELL (was 1.6×, caused narrow corridors)
- Removed tunnel overlay (was painting dark navy over tile cells)
- Palace drawn at 6×4 cells (cols 7–12, rows 7–10) on gray tile base
- Palace maze footprint: col 7 rows 7–10 made WALL so operative can't walk through
- Removed "TEHRAN HQ" text label overlay from palace

### UI / Audio
- Sound 🔊/🔇 toggle button added to HUD
- Music starts on first ENTER/SPACE keypress

### Gameplay
- Jet exit: operative now emerges at jet's last position, not trapdoor entry point

---

## Current State / Known Issues

### Palace (HQ) — MAIN REMAINING TASK
The palace is the biggest pending redesign. Two problems:

1. **Palace doesn't touch surrounding buildings** — it floats in the maze surrounded by path corridors. It should be flush against adjacent wall cells (buildings) on its sides, with paths only at specific entrances.

2. **Corridors are too wide** — paths should never be more than 1 cell wide. Currently some areas have 2+ cell wide corridors.

### Plan for Next Session: Maze Redesign

#### Goals
- Palace (cols 7–12, rows 7–10) should be directly bordered by building cells on LEFT, RIGHT, and TOP
- Only one entrance/exit: top-center (the DOOR row, row 7, cols 9–11)
- All corridors exactly 1 cell wide — no double-width paths anywhere
- Maintain tunnel row (row 9) on left/right edges
- Maintain 4 MASK positions (power-ups) roughly at corners

#### Approach (do in chunks)
1. **Chunk 1**: Redesign rows 6–11 (the HQ surrounding area) — make palace flush against buildings
2. **Chunk 2**: Audit all other rows for double-wide corridors, fix one section at a time
3. **Chunk 3**: Test walkability — make sure all dots are reachable, no dead ends that trap player
4. **Chunk 4**: Verify enemy AI still navigates correctly (return-to-HQ path not broken)

#### Key Maze Constants
```
COLS = 19, ROWS = 21
WALL=1, DOT=0, MASK=2, EMPTY=3, HQ=4, DOOR=5
HQ area: cols 7–12, rows 7–10 (skip in drawMaze)
Tunnel row: row 9 (cols 0–3 and 17–18 are EMPTY=3)
Enemy spawn: ctr(10, 9) → col 10, row 9
```

#### Current BASE maze (for reference)
```javascript
const BASE = [
  [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],  // row 0
  [1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,1],  // row 1
  [1,0,1,1,0,1,1,0,0,1,0,0,1,1,0,1,1,0,1],  // row 2
  [1,2,1,1,0,1,1,0,0,1,0,0,1,1,0,1,1,2,1],  // row 3
  [1,0,1,1,0,1,1,0,0,0,0,0,0,0,0,1,1,0,1],  // row 4
  [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],  // row 5
  [1,0,1,1,0,1,1,0,1,0,0,0,1,0,1,1,0,0,1],  // row 6
  [1,0,1,1,0,1,1,1,1,5,5,5,1,0,1,1,0,0,1],  // row 7  ← DOOR row (col 7 now WALL)
  [1,0,0,0,0,0,0,1,1,4,4,4,1,0,0,0,0,0,1],  // row 8  ← col 7 now WALL
  [3,3,3,3,0,1,1,1,1,4,4,4,1,0,1,1,0,3,3],  // row 9  ← tunnel + col 7 WALL
  [1,1,1,1,0,1,1,1,1,4,4,4,1,0,1,1,0,1,1],  // row 10 ← col 7 now WALL
  [1,0,0,0,0,0,0,0,1,1,1,1,1,0,0,0,0,0,1],  // row 11
  [1,0,1,1,0,1,1,0,0,0,1,0,0,0,1,1,0,0,1],  // row 12
  [1,0,1,1,0,1,1,0,0,0,1,0,0,0,1,1,0,0,1],  // row 13
  [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],  // row 14
  [1,0,1,1,0,1,1,0,1,1,1,1,1,0,1,1,0,0,1],  // row 15
  [1,2,1,1,0,1,1,0,1,1,1,1,1,0,1,1,0,2,1],  // row 16
  [1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1],  // row 17
  [1,0,1,1,0,1,1,0,1,0,1,0,1,0,1,1,0,0,1],  // row 18
  [1,0,1,1,0,1,1,0,1,3,3,3,1,0,1,1,0,0,1],  // row 19
  [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],  // row 20
];
```

---

## Files Reference
- `index.html` — main game (all code in one file)
- `assets/hq/compound_00.png` — palace sprite (384×256)
- `assets/player/operative_walk_side_00..07.png`
- `assets/enemies/` — all enemy sprites (ayatollah, guard, basij, female + scared variants + ayatollah side)
- `assets/tiles/street_tiles_00..05.png` (exclude index 3)
- `assets/buildings_a/buildings_a_00..05.png`
- `assets/Desert_Caravan_Uprising.mp3`
- `cut_sprites.py` — sprite cutting tool

## Git Status
- Last commit: `25094dd` — "Fix sprite directions, tunnel blacks, passages, and add sound toggle"
- Uncommitted changes: tile fixes, palace image, maze col-7 blocking, sound toggle, emerge-at-jet-position
