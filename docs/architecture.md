# Architecture - ecoran_fuel_monitor

## Overview

The app keeps the existing multi-window Assetto Corsa Python structure:

- `Ecoran Main`
- `Ecoran Power`
- `Ecoran Lap`
- `Ecoran BSFC`
- `Ecoran Debug`

The windows are now split more aggressively by purpose:

- Main: three HUD values only
- Power: 20-second trend + stacked contribution bar + residual integral
- BSFC: compact operating-point learning screen
- Lap: comparison table
- Debug: audit view + gate editor / recorder controls

## Runtime Data Flow

The runtime loop is still:

1. refresh shared memory
2. read telemetry into `state`
3. update smoothed / inferred demand values
4. append histories
5. update lap tracker and measurement session
6. refresh window labels
7. let render callbacks paint graph/table/HUD backgrounds

The main entry remains [`ecoran_fuel_monitor.py`].

## Main Responsibilities

### Main HUD

Main intentionally dropped all detailed rows.

It now shows only:

- average fuel economy
- pace delta
- engine ON/OFF
- four small corner buttons: `PWR`, `LAP`, `BSFC`, `DBG`

Everything else that used to live in Main was moved to Debug.

### Power Window

Power uses three vertical layers:

1. 20-second time-series graph
2. one centered stacked bar for current contribution breakdown
3. residual integral sparkline

`app_state._HIST_LEN` is now `200`, which keeps 20 seconds at the existing
10 Hz update cadence.

Auto-scale is based on recent history rather than a hard 2000 W floor.

### BSFC Window

BSFC now combines:

- one-line current summary
- heatmap with cell values
- 20-second fading trace
- current operating point
- candidate operating points for other forward gears

Engine OFF dims the whole view without hiding the map.

### Lap Window

Lap is a compact comparison table with:

- explicit column borders
- a provisional row background
- color grading across completed rows for best/worst values

### Debug Window

Debug is the long-form audit window.

Sections:

1. Session Summary
2. Live Vehicle
3. Demand / Model
4. Estimate / Race
5. Raw Source
6. Gate Control

## Measurement and Lap Tracking

### Legacy Measurement

Legacy start logic still exists:

- `session_start`
- `first_cross_sf`
- `manual_arm_then_cross_sf`

If gate-based recording is not active, the old SF-based measurement flow is
still used.

### Gate-Based Recording

Gate-based recording adds:

- `record_mode = manual | semi_auto`
- `record_state = idle | armed | running | finished`

Manual mode:

- `START` begins measurement
- `STOP` finishes measurement
- lap count advances on lap-gate crossings only

Semi-auto mode:

- `ARM` enters `armed`
- start gate crossing enters `running`
- lap gate crossing completes a lap
- finish gate crossing ends the run

Gate-based control overrides legacy measurement start modes only when it is
active.

### Lap Tracker Integration

`modules/lap_tracker.py` still owns session distance and lap-distance based
progress. It now supports gate-based lap completion in addition to the legacy
start/finish crossing path.

This keeps:

- measurement distance
- current lap distance
- provisional 8-lap estimate inputs

compatible with the existing logic.

## Gate Model

Each gate is a line segment described by:

- `center_world`
- `forward_world`
- `tangent_world`
- `half_width_m`
- `directional`
- `cooldown_s`
- `min_speed_kmh`
- `enabled`

Detection is performed on the XZ plane.

Directional pass condition:

```text
s0 = dot(p0 - c, n)
s1 = dot(p1 - c, n)

cross when s0 < 0 and s1 >= 0
```

Width condition:

```text
u = dot(p1 - c, t)
abs(u) <= half_width_m
```

Cooldown and minimum-speed guards are checked before a trigger is accepted.

Finish-gate triggers are also guarded by:

- `minimum_valid_run_time_s`
- `minimum_valid_finish_lap_count`

## Gate Storage

Gates are stored in JSON under:

```text
config/gates/<track_key>.json
```

`track_key` currently comes from AC shared memory:

- `static.track`
- `static.trackConfiguration`

The app:

- auto-saves after edit operations
- auto-loads on track/layout change
- survives broken JSON by falling back to an empty gate state

## Render Callback Ownership

- `panel_main.render()` paints the HUD shell
- `graph_renderer.draw()` paints the Power trend graph
- `gauge_renderer.draw()` paints the Power stacked bar and residual sparkline
- `bsfc_renderer.draw()` paints the BSFC map and overlays
- `panel_lap.render()` paints the table background and borders

This keeps label layout and GL painting separate while preserving the existing
render-callback model.
