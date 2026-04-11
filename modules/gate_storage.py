# modules/gate_storage.py
# JSON storage helpers for per-track gate definitions.

import json
import os

from modules.gate_model import normalize_gate, serialize_gate


def _app_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def gates_dir():
    return os.path.join(_app_root(), "config", "gates")


def gate_file_path(track_key):
    return os.path.join(gates_dir(), "{0}.json".format(str(track_key or "unknown_track")))


def save_gates(track_key, record_mode, gates):
    if not track_key:
        return False, "track_key missing", ""

    payload = {
        "version": 1,
        "track_key": str(track_key),
        "mode_defaults": {
            "record_mode": str(record_mode or "manual"),
        },
        "gates": {},
    }

    for kind in ("start", "lap", "finish"):
        gate = serialize_gate(gates.get(kind)) if isinstance(gates, dict) else None
        if gate is not None:
            payload["gates"][kind] = gate

    path = gate_file_path(track_key)
    try:
        directory = os.path.dirname(path)
        if directory and not os.path.isdir(directory):
            os.makedirs(directory)
        with open(path, "w") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
        return True, "saved", path
    except Exception as exc:
        return False, str(exc), path


def load_gates(track_key):
    path = gate_file_path(track_key)
    if not track_key:
        return False, {"record_mode": "manual", "gates": {}}, "track_key missing", path
    if not os.path.isfile(path):
        return False, {"record_mode": "manual", "gates": {}}, "not_found", path

    try:
        with open(path, "r") as handle:
            payload = json.load(handle)
    except Exception as exc:
        return False, {"record_mode": "manual", "gates": {}}, str(exc), path

    result = {
        "record_mode": str(payload.get("mode_defaults", {}).get("record_mode", "manual")),
        "gates": {},
    }
    for kind in ("start", "lap", "finish"):
        result["gates"][kind] = normalize_gate(kind, payload.get("gates", {}).get(kind))
    return True, result, "loaded", path
