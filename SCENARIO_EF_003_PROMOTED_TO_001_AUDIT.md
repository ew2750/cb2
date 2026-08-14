# E/F scenario 003 promoted to scenario 001

The filtered scenario 003 layouts for run sets E and F were selected to replace
their previous scenario 001 layouts. All eight `t0`-`t3` by `l0`-`l1` files
were renamed from `scenario_0003_*` to `scenario_0001_*`. The temporary restored
scenario 002 files and the superseded scenario 001 layouts were removed.

| Current run set/scenario | Source layout | Cards retained | Targets retained |
|---|---|---:|---:|
| E/001 | E/003 | 59 | 8 |
| F/001 | F/003 | 59 | 7 |

Both layouts are native 12x12 materials. Cards outside the map and pink cards
have been removed, former pink-house cells use `GROUND_TILE_PATH` (asset ID 28),
and instructions with unavailable targets or required landmarks are excluded.
