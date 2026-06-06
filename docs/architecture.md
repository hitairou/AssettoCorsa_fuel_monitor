# Architecture - ecoran_fuel_monitor

## Overview

`ecoran_fuel_monitor` no longer uses one oversized translucent app window with
all sections painted into the same coordinate space. That older design made it
too easy to overlap Summary, power graphics, lap data, and BSFC analysis, and
it also blurred the difference between "always watch while driving" data and
"open later for analysis" data.

The app now uses multiple AC Python windows:

- `Ecoran Main`
- `Ecoran Power`
- `Ecoran Lap`
- `Ecoran BSFC`
- `Ecoran Debug`

Each window owns one responsibility area. Every renderer draws in local
window-space coordinates only. No section draws onto a shared giant gray
background.

## Data Meaning Categories

All runtime values are organized into four meaning groups.

### Observed / Actual

Values read directly from shared memory or values that only make sense while
the engine is actually running.

Examples:
- `observed_rpm`
- `raw_gear`
- `display_gear`
- `observed_speed_kmh`
- `observed_engine_on`
- `observed_fuel`

### Demand / Inferred

Values reverse-calculated from current motion, grade, acceleration, and gear.
These are not ECU-reported outputs.

Examples:
- `demand_wheel_power_w`
- `demand_engine_power_w`
- `demand_load_ratio`
- `demand_bsfc_g_per_kwh`
- `demand_fuel_flow_ml_s`

### Estimate / Projection

Future-looking values derived from completed history and, optionally, the
current provisional lap.

Examples:
- `est_8lap_fuel_ml_completed_only`
- `est_8lap_fuel_ml_dynamic`
- `est_8lap_econ_km_per_l_completed_only`
- `est_8lap_econ_km_per_l_dynamic`
- `est_8lap_source`

### Aggregate / Cumulative

Measurement-session totals and averages.

Examples:
- `avg_fuel_econ_km_per_l`
- `avg_speed_kmh`
- `measurement_fuel_used_ml`
- `lap_rows`
- `laps_completed`

## Measurement Session

The app now separates the AC session from the measurement session.

`measurement session` is the analysis zero-point used for:

- `Avg Fuel Econ`
- `Avg Speed`
- `Fuel Used`
- `Pace Delta`
- `Remaining`
- 8-lap estimates
- lap table rows

Supported start modes:

- `session_start`
- `first_cross_sf`
- `manual_arm_then_cross_sf`

Default is `first_cross_sf`.

That means entering the session does not immediately start race analysis.
Instead, the first start/finish crossing becomes measurement zero so that pit
exit and pre-start motion do not contaminate averages or lap history.

## Initial Partial Lap Handling

The lap table ignores the initial partial lap when
`ignore_initial_partial_lap = 1`.

Reason:
- starting from pit or a random spawn point often means "Lap 1" is not a full
  race lap
- saving that partial lap as a completed row corrupts average lap fuel and
  8-lap estimation

The tracker therefore waits for the first valid start/finish crossing before it
begins storing completed-lap rows.

## Window Responsibilities

### Ecoran Main

Purpose: always-visible monitoring while driving.

Blocks:
- `Summary`
- `Live / Current`

Summary values:
- `Avg Fuel Econ [km/L]`
- `Avg Speed [km/h]`
- `Remaining [mm:ss.s]`
- `Pace Delta [s]`
- `Fuel Used [mL]`
- `Laps Completed / Total`

Live / Current values:
- `RPM`
- `Display Gear`
- `Throttle [%]`
- `Grade [%]`
- `Engine`
- `Demand Load [%]`
- `Current BSFC [g/kWh]`
- `Fuel Flow [mL/s]`
- `8lap Fuel Est [mL]`
- `8lap Econ Est [km/L]`
- `Net Energy Balance [kJ]`

Engine-off display rule:
- `Current BSFC` becomes `---`
- `Fuel Flow` becomes `0.0000`
- demand values may still exist internally and remain visible in Debug

### Ecoran Power

Purpose: demand-power and residual-balance analysis.

Content:
- 10-second demand-power graph
- diverging bar chart
- `Net Energy Balance [kJ]`

Series meanings:
- `Engine Demand [W]`
- `Rolling Resistance [W]`
- `Aero Drag [W]`
- `Acceleration Term [W]`
- `Grade Term [W]`

Important:
- `Engine Demand` and `Wheel Demand` are reverse-calculated demand values
- they are not measured engine output values
- zero line is the sign split for positive and resistive terms

### Ecoran Lap

Purpose: lap-to-lap comparison under the measurement-session rules.

Columns:
- `Lap`
- `Fuel Econ [km/L]`
- `Fuel Used [mL]`
- `Avg Speed [km/h]`
- `Engine Energy [kJ]`
- `Roll Energy [kJ]`
- `Aero Energy [kJ]`
- `Accel Energy [kJ]`
- `Grade Energy [kJ]`
- `Restart Count`
- `Engine ON Ratio [%]`

The table no longer uses a separate provisional-only row widget. The bottom
row slot is reused for the current provisional lap and prefixed with `>`.

### Ecoran BSFC

Purpose: actual engine operating-point analysis.

Content:
- BSFC heatmap
- current point
- last 10 seconds trace in wall-clock time
- axis labels for RPM and load

Engine-off rule:
- `Current RPM` displays `0`
- `Current Load` displays `---`
- `Current BSFC` displays `---`
- current map point is hidden
- trace keeps wall-clock continuity by inserting gaps while engine-off

### Ecoran Debug

Purpose: auditability for raw values, demand values, and estimate source.

Content includes:
- raw vs display gear
- raw RPM
- grade source
- vertical-axis selection
- raw coordinates / distance / pitch
- demand load / BSFC / fuel flow
- estimate source
- current lap progress
- restart count
- engine-on ratio

## Net Energy Balance

`Net Energy Balance [kJ]` is the time integral of:

`P_engine_demand - P_roll - P_aero - P_accel - P_grade`

It is not kinetic energy and not a stored physical energy state.

Interpret it as a residual of the current power-balance model, not as a real
"battery" or "energy tank".

## Presets and Visibility

Each window has its own show/hide flag:

- `ui_show_main_window`
- `ui_show_power_window`
- `ui_show_lap_window`
- `ui_show_bsfc_window`
- `ui_show_debug_window`

Presets:
- `overview`: main only
- `analysis`: main + power
- `lap`: main + lap
- `bsfc`: main + bsfc
- `debug`: main + power + debug
- `custom`: any manual combination

The Main window exposes the preset cycle button and per-window toggles. When
`measurement_start_mode = manual_arm_then_cross_sf`, the Main window also shows
an `ARM` button.

## Data Flow

Runtime order remains:

```text
shared memory
  -> telemetry_reader.read_telemetry()
  -> grade_estimator.update()
  -> forces.calc_forces()
  -> rpm_load.calc_load()
  -> bsfc_interp.query()
  -> fuel_integrator.compute_fuel_flow()
  -> lap_tracker.update()
  -> strategy_metrics.build_8lap_estimate()
  -> window_manager.update_windows()
```

## Persistence

Window positions, sizes, visibility, and current preset are stored in:

```text
%LOCALAPPDATA%\ecoran_fuel_monitor\ui_state.json
```
