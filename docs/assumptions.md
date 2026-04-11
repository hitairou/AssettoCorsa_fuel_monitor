# Assumptions and Modeling Notes - ecoran_fuel_monitor

## 1. Demand Values Are Model Outputs

`Demand Load`, `Demand BSFC`, `Demand Fuel Flow`, and the Power window's
component breakdown are reverse-calculated model values, not ECU measurements.

## 2. Main HUD Is Intentionally Sparse

Main is for driving-time recognition, not full telemetry inspection.
Detailed values were moved into Debug on purpose.

## 3. Power Residual Is Not Physical Stored Energy

`Residual Int.` / `Net Energy Balance` is the integral of the model residual:

```text
P_engine_demand - P_roll - P_aero - P_accel - P_grade
```

It is not kinetic energy, fuel energy, or a battery state.

## 4. BSFC Current Point Visibility

Current BSFC / load are only shown when the engine operating point is
meaningful. Engine OFF dims the BSFC view and hides the current point if the
operating point is invalid.

## 5. Gate Detection Uses XZ Plane Only

Gate crossing is evaluated on the XZ plane.

- `center_world` keeps Y for storage/reference
- pass/fail ignores height
- `forward_world` and `tangent_world` are normalized in XZ

## 6. Directional Gate Meaning

Directional gates use:

```text
s0 = dot(p0 - c, n)
s1 = dot(p1 - c, n)
```

and trigger only when:

```text
s0 < 0 and s1 >= 0
```

So the gate remembers the intended forward crossing direction.

## 7. Gate Forward Vector Source

Gate creation prefers the car heading from AC shared memory and aligns it with
the current horizontal velocity when possible. This keeps stopped-car gate
creation usable while still following the actual travel direction in motion.

## 8. False-Trigger Guards

Each gate can reject a pass due to:

- cooldown
- minimum speed
- being outside half-width
- wrong record state
- finish guard (minimum run time / completed laps)

These rejection reasons are surfaced in Debug.

## 9. Legacy Measurement Compatibility

Legacy SF-based measurement still exists when gate-based recording is not
active. The Debug window exposes a small legacy ARM control for
`manual_arm_then_cross_sf` so old configurations still work.

## 10. Runtime Constraints

The app still targets Assetto Corsa's embedded Python runtime:

- no external packages
- standard library only
- multi-window AC UI callbacks preserved
