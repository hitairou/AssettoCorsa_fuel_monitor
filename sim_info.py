# sim_info.py - Assetto Corsa Shared Memory Reader
# Based on the standard AC sim_info implementation.
# Compatible with AC Python app environment (Python 2.7/3.x).
#
# Usage:
#   from sim_info import info
#   speed = info.physics.speedKmh
#   lap   = info.graphics.completedLaps

import mmap
import ctypes
import os
import sys

# ---------------------------------------------------------------------------
# Attempt to load _ctypes from the app's third_party directory if not found
# ---------------------------------------------------------------------------
_app_dir = os.path.dirname(os.path.abspath(__file__))
_third_party = os.path.join(_app_dir, "third_party")
if _third_party not in sys.path:
    sys.path.insert(0, _third_party)


# ---------------------------------------------------------------------------
# Struct definitions matching AC shared memory layout
# ---------------------------------------------------------------------------

class SPageFilePhysics(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("packetId",            ctypes.c_int),
        ("gas",                 ctypes.c_float),
        ("brake",               ctypes.c_float),
        ("fuel",                ctypes.c_float),
        ("gear",                ctypes.c_int),
        ("rpms",                ctypes.c_int),
        ("steerAngle",          ctypes.c_float),
        ("speedKmh",            ctypes.c_float),
        ("velocity",            ctypes.c_float * 3),
        ("accG",                ctypes.c_float * 3),
        ("wheelSlip",           ctypes.c_float * 4),
        ("wheelLoad",           ctypes.c_float * 4),
        ("wheelsPressure",      ctypes.c_float * 4),
        ("wheelAngularSpeed",   ctypes.c_float * 4),
        ("tyreWear",            ctypes.c_float * 4),
        ("tyreDirtyLevel",      ctypes.c_float * 4),
        ("tyreCoreTemperature", ctypes.c_float * 4),
        ("camberRAD",           ctypes.c_float * 4),
        ("suspensionTravel",    ctypes.c_float * 4),
        ("drs",                 ctypes.c_float),
        ("tc",                  ctypes.c_float),
        ("heading",             ctypes.c_float),
        ("pitch",               ctypes.c_float),
        ("roll",                ctypes.c_float),
        ("cgHeight",            ctypes.c_float),
        ("carDamage",           ctypes.c_float * 5),
        ("numberOfTyresOut",    ctypes.c_int),
        ("pitLimiterOn",        ctypes.c_int),
        ("abs",                 ctypes.c_float),
        ("kersCharge",          ctypes.c_float),
        ("kersInput",           ctypes.c_float),
        ("autoShifterOn",       ctypes.c_int),
        ("rideHeight",          ctypes.c_float * 2),
        ("turboBoost",          ctypes.c_float),
        ("ballast",             ctypes.c_float),
        ("airDensity",          ctypes.c_float),
        ("airTemp",             ctypes.c_float),
        ("roadTemp",            ctypes.c_float),
        ("localAngularVel",     ctypes.c_float * 3),
        ("finalFF",             ctypes.c_float),
        ("performanceMeter",    ctypes.c_float),
        ("engineBrake",         ctypes.c_int),
        ("ersRecoveryLevel",    ctypes.c_int),
        ("ersPowerLevel",       ctypes.c_int),
        ("ersHeatCharging",     ctypes.c_int),
        ("ersIsCharging",       ctypes.c_int),
        ("kersCurrentKJ",       ctypes.c_float),
        ("drsAvailable",        ctypes.c_int),
        ("drsEnabled",          ctypes.c_int),
        ("brakeTemp",           ctypes.c_float * 4),
        ("clutch",              ctypes.c_float),
        ("tyreTempI",           ctypes.c_float * 4),
        ("tyreTempM",           ctypes.c_float * 4),
        ("tyreTempO",           ctypes.c_float * 4),
        ("isAIControlled",      ctypes.c_int),
        ("tyreContactPoint",    ctypes.c_float * 4 * 3),
        ("tyreContactNormal",   ctypes.c_float * 4 * 3),
        ("tyreContactHeading",  ctypes.c_float * 4 * 3),
        ("brakeBias",           ctypes.c_float),
        ("localVelocity",       ctypes.c_float * 3),
    ]


class SPageFileGraphic(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("packetId",                ctypes.c_int),
        ("status",                  ctypes.c_int),
        ("session",                 ctypes.c_int),
        ("currentTime",             ctypes.c_wchar * 15),
        ("lastTime",                ctypes.c_wchar * 15),
        ("bestTime",                ctypes.c_wchar * 15),
        ("split",                   ctypes.c_wchar * 15),
        ("completedLaps",           ctypes.c_int),
        ("position",                ctypes.c_int),
        ("iCurrentTime",            ctypes.c_int),
        ("iLastTime",               ctypes.c_int),
        ("iBestTime",               ctypes.c_int),
        ("sessionTimeLeft",         ctypes.c_float),
        ("distanceTraveled",        ctypes.c_float),
        ("isInPit",                 ctypes.c_int),
        ("currentSectorIndex",      ctypes.c_int),
        ("lastSectorTime",          ctypes.c_int),
        ("numberOfLaps",            ctypes.c_int),
        ("tyreCompound",            ctypes.c_wchar * 33),
        ("replayTimeMultiplier",    ctypes.c_float),
        ("normalizedCarPosition",   ctypes.c_float),
        ("carCoordinates",          ctypes.c_float * 3),
        ("penaltyTime",             ctypes.c_float),
        ("flag",                    ctypes.c_int),
        ("idealLineOn",             ctypes.c_int),
        ("isInPitLane",             ctypes.c_int),
        ("surfaceGrip",             ctypes.c_float),
        ("mandatoryPitDone",        ctypes.c_int),
        ("windSpeed",               ctypes.c_float),
        ("windDirection",           ctypes.c_float),
    ]


class SPageFileStatic(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("smVersion",           ctypes.c_wchar * 15),
        ("acVersion",           ctypes.c_wchar * 15),
        ("numberOfSessions",    ctypes.c_int),
        ("numCars",             ctypes.c_int),
        ("carModel",            ctypes.c_wchar * 33),
        ("track",               ctypes.c_wchar * 33),
        ("playerName",          ctypes.c_wchar * 33),
        ("playerSurname",       ctypes.c_wchar * 33),
        ("playerNick",          ctypes.c_wchar * 33),
        ("sectorCount",         ctypes.c_int),
        ("maxTorque",           ctypes.c_float),
        ("maxPower",            ctypes.c_float),
        ("maxRpm",              ctypes.c_int),
        ("maxFuel",             ctypes.c_float),
        ("suspensionMaxTravel", ctypes.c_float * 4),
        ("tyreRadius",          ctypes.c_float * 4),
        ("maxTurboBoost",       ctypes.c_float),
        ("deprecated_1",        ctypes.c_float),
        ("deprecated_2",        ctypes.c_float),
        ("penaltiesEnabled",    ctypes.c_int),
        ("aidFuelRate",         ctypes.c_float),
        ("aidTireRate",         ctypes.c_float),
        ("aidMechanicalDamage", ctypes.c_float),
        ("aidAllowTyreBlankets",ctypes.c_int),
        ("aidStability",        ctypes.c_float),
        ("aidAutoClutch",       ctypes.c_int),
        ("aidAutoBlip",         ctypes.c_int),
        ("hasDRS",              ctypes.c_int),
        ("hasERS",              ctypes.c_int),
        ("hasKERS",             ctypes.c_int),
        ("kersMaxJ",            ctypes.c_float),
        ("engineBrakeSettingsCount", ctypes.c_int),
        ("ersPowerControllerCount", ctypes.c_int),
        ("trackSPlineLength",   ctypes.c_float),
        ("trackConfiguration",  ctypes.c_wchar * 33),
        ("ersMaxJ",             ctypes.c_float),
        ("isTimedRace",         ctypes.c_int),
        ("hasExtraLap",         ctypes.c_int),
        ("carSkin",             ctypes.c_wchar * 33),
        ("reversedGridPositions", ctypes.c_int),
        ("PitWindowStart",      ctypes.c_int),
        ("PitWindowEnd",        ctypes.c_int),
    ]


# ---------------------------------------------------------------------------
# SimInfo wrapper
# ---------------------------------------------------------------------------

class SimInfo(object):
    def __init__(self):
        self._physics_mmap = None
        self._graphics_mmap = None
        self._static_mmap = None
        self._connected = False

        self.physics  = SPageFilePhysics()
        self.graphics = SPageFileGraphic()
        self.static   = SPageFileStatic()

        self._try_connect()

    def _try_connect(self):
        try:
            self._physics_mmap  = mmap.mmap(0, ctypes.sizeof(SPageFilePhysics),
                                             "Local\\acpmf_physics")
            self._graphics_mmap = mmap.mmap(0, ctypes.sizeof(SPageFileGraphic),
                                             "Local\\acpmf_graphics")
            self._static_mmap   = mmap.mmap(0, ctypes.sizeof(SPageFileStatic),
                                             "Local\\acpmf_static")
            self._connected = True
        except Exception:
            self._connected = False

    @property
    def connected(self):
        return self._connected

    def update(self):
        if not self._connected:
            self._try_connect()
            return

        try:
            self._physics_mmap.seek(0)
            ctypes.memmove(ctypes.addressof(self.physics),
                           self._physics_mmap.read(ctypes.sizeof(SPageFilePhysics)),
                           ctypes.sizeof(SPageFilePhysics))

            self._graphics_mmap.seek(0)
            ctypes.memmove(ctypes.addressof(self.graphics),
                           self._graphics_mmap.read(ctypes.sizeof(SPageFileGraphic)),
                           ctypes.sizeof(SPageFileGraphic))

            self._static_mmap.seek(0)
            ctypes.memmove(ctypes.addressof(self.static),
                           self._static_mmap.read(ctypes.sizeof(SPageFileStatic)),
                           ctypes.sizeof(SPageFileStatic))
        except Exception:
            self._connected = False

    def close(self):
        for m in (self._physics_mmap, self._graphics_mmap, self._static_mmap):
            if m is not None:
                try:
                    m.close()
                except Exception:
                    pass
        self._connected = False


# Singleton instance
info = SimInfo()
