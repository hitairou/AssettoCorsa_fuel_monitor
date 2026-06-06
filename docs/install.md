# Installation Guide - ecoran_fuel_monitor

## Prerequisites

- Assetto Corsa (Steam)
- Target car installed

## Install Path

Copy `apps/python/ecoran_fuel_monitor/` to:

```text
C:\Program Files (x86)\Steam\steamapps\common\assettocorsa\apps\python\ecoran_fuel_monitor\
```

Expected structure:

```text
ecoran_fuel_monitor\
├─ ecoran_fuel_monitor.py
├─ sim_info.py
├─ config\
├─ docs\
└─ modules\
```

## Enable the App

1. Start Assetto Corsa.
2. Open `Options -> General -> UI Modules`.
3. Enable `ecoran_fuel_monitor`.

Only the main module needs to be enabled here. The additional Power, Lap,
BSFC, and Debug windows are created by the same script at runtime.

## First Launch

1. Enter a driving session.
2. Open the app shelf.
3. Launch `ecoran_fuel_monitor`.
4. Use the Main window buttons to show `PWR`, `LAP`, `BSFC`, or `DBG`.

Default startup preset is `overview`, so only `Ecoran Main` is visible unless
another preset or a saved layout is restored.

## Persisted Layout

The app stores window positions, sizes, and visibility here:

```text
%LOCALAPPDATA%\ecoran_fuel_monitor\ui_state.json
```

To force the configured startup preset every time, set `ui.restore_state = 0`
in `strategy.ini`.

## Verification

A healthy startup should show:

- `Ecoran Main` with summary and live details
- no overlapping giant gray background
- Power/Lap/BSFC/Debug windows opening independently when toggled
- telemetry values updating while driving

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| App not listed in UI Modules | Wrong install path | Verify `apps/python/ecoran_fuel_monitor/` |
| Main window opens but others do not | Preset still hides them | Use `PWR`, `LAP`, `BSFC`, `DBG` buttons |
| All values remain `---` | Session not fully loaded or SHM not ready | Enter a live session and retry |
| AC crashes when opening a window | Installed files out of sync with repo | recopy the full app folder |
| Layout resets every launch | `ui.restore_state = 0` or save failure | enable restore or check `%LOCALAPPDATA%` write access |
