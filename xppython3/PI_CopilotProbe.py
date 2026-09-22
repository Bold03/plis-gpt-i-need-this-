"""Optional XPPython3 probe plugin.

Install into: X-Plane 12/Resources/plugins/PythonPlugins/PI_CopilotProbe.py
"""
from XPPython3 import xp

DATAREF_CANDIDATES = [
    "sim/flightmodel/failures/onground_any",
    "sim/flightmodel/position/groundspeed",
    "sim/cockpit2/gauges/indicators/radio_altimeter_height_ft_pilot",
    "sim/cockpit2/gauges/indicators/altitude_ft_pilot",
    "sim/cockpit2/gauges/indicators/airspeed_kts_pilot",
    "sim/cockpit2/electrical/battery_on",
    "laminar/B738/autobrake/autobrake_pos",
    "laminar/B738/toggle_switch/irs_left",
    "laminar/B738/toggle_switch/irs_right",
]

COMMAND_CANDIDATES = [
    "sim/flight_controls/landing_gear_up",
    "sim/flight_controls/landing_gear_down",
    "sim/flight_controls/flaps_up",
    "sim/flight_controls/flaps_down",
    "laminar/B738/switch/battery_dn",
    "laminar/B738/switch/battery_up",
    "laminar/B738/knob/autobrake_up",
    "laminar/B738/knob/autobrake_dn",
]

class PythonInterface:
    def XPluginStart(self):
        return ("B737 Copilot Probe", "ai.openai.reference.b737copilot.probe", "Checks candidate datarefs and commands")

    def XPluginEnable(self):
        xp.log("[B737CopilotProbe] starting capability probe")
        for name in DATAREF_CANDIDATES:
            ref = xp.findDataRef(name)
            xp.log(f"[B737CopilotProbe] DATAREF {'OK' if ref else 'MISS'} {name}")
        for name in COMMAND_CANDIDATES:
            ref = xp.findCommand(name)
            xp.log(f"[B737CopilotProbe] COMMAND {'OK' if ref else 'MISS'} {name}")
        xp.log("[B737CopilotProbe] probe complete")
        return 1

    def XPluginDisable(self):
        pass

    def XPluginStop(self):
        pass

    def XPluginReceiveMessage(self, inFromWhom, inMessage, inParam):
        pass
