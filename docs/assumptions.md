# Assumptions and Modeling Notes - ecoran_fuel_monitor

## 1. Demand Load

`Demand Load [%]` is the required load ratio inferred from current vehicle
motion and gearing.

It is not an ECU-reported load value.

## 2. Engine Demand / Wheel Demand

`Engine Demand [W]` and `Wheel Demand [W]` are reverse-calculated demand powers.
They describe the power required by the current motion state under the model.

They are not measured engine output.

## 3. Current BSFC Display

`Current BSFC` is only shown when the engine operating point is meaningful:

- engine considered ON
- display gear engaged
- RPM above display threshold

When that condition is false, the UI hides current BSFC and load because the
remaining model outputs are demand-only values.

## 4. Demand BSFC / Fuel Flow

`demand_bsfc_g_per_kwh` and `demand_fuel_flow_ml_s` may still be computed while
the engine is OFF. They are retained for debugging and audit purposes but are
not shown as live engine operating values in the Main or BSFC windows.

## 5. Dynamic 8-Lap Estimate

The dynamic estimate uses the current provisional lap only when both conditions
are met:

- `current_lap_progress >= min_progress_for_dynamic_estimate`
- `current_lap_time >= min_time_for_dynamic_estimate`

If those conditions are not met, the display falls back to completed laps only.

## 6. Initial Partial Lap Exclusion

When `ignore_initial_partial_lap = 1`, the lap tracker does not store the
pre-measurement partial lap as a completed row. This avoids contaminating lap
history with pit-exit or mid-track spawn conditions.

## 7. Net Energy Balance

`Net Energy Balance [kJ]` is the integral of the power-balance residual.

It is not:
- kinetic energy
- fuel energy
- a stored physical energy state

It is a model residual intended for analysis.

## 8. Gear Mapping

Assetto Corsa raw gear values may differ from the stock HUD display by a fixed
offset on a given car. The app therefore separates:

- `raw_gear`
- `display_gear`

and applies `gear_display_offset` in the display path.

## 9. Fuel Density

Fuel-flow conversion uses `fuel_density_g_per_ml` from `vehicle.ini`. The app
falls back to `0.778` only when that config value is missing.

## 10. Grade Estimation

Dynamic grade estimation still depends on telemetry consistency:

- `distanceTraveled`
- `carCoordinates`
- `pitch`
- chosen `vertical_axis_index`

The Debug window exposes the raw values so the estimator can be audited on the
target car and track.

## 11. Python Runtime Constraints

The app still targets Assetto Corsa's embedded Python runtime:

- no external packages
- no type annotations
- standard library only
