#!/usr/bin/env python3
"""
Temperature-based fan controller for Radxa Penta SATA HAT on Raspberry Pi 5.
Uses lgpio (Pi 5's official GPIO library) instead of the deprecated gpiod v1 API.
"""

import time
import subprocess
import lgpio

# -------------------------------------------------------
# CONFIG
# -------------------------------------------------------
CHIP = 0               # gpiochip0 — Radxa HAT works through this
LINE = 27              # Radxa Penta SATA HAT fan pin
CHECK_INTERVAL = 2.0   # seconds between temp checks
HYST = 2.0             # hysteresis (°C)


def temp_to_duty(t):
    """Quiet fan curve — stays silent until 55°C."""
    if t < 55:
        return 0      # silent
    elif t < 60:
        return 20     # whisper
    elif t < 65:
        return 35     # low
    elif t < 70:
        return 50     # medium-low
    elif t < 75:
        return 65     # medium
    elif t < 85:
        return 80     # high
    else:
        return 100    # full power for protection


# -------------------------------------------------------
# Helpers
# -------------------------------------------------------
def get_cpu_temp():
    """Returns CPU temperature in °C as float."""
    try:
        out = subprocess.check_output(
            ["vcgencmd", "measure_temp"]
        ).decode()
        return float(out.replace("temp=", "").replace("'C", ""))
    except Exception:
        # Fallback to thermal zone
        try:
            with open("/sys/class/thermal/thermal_zone0/temp") as f:
                return float(f.read().strip()) / 1000.0
        except:
            return 0.0


def temp_threshold_for_duty(duty):
    """Return the temperature that triggers this duty level."""
    thresholds = {0: 0, 20: 55, 35: 60, 50: 65, 65: 70, 80: 75, 100: 85}
    return thresholds.get(duty, 0)


def apply_hysteresis(t, target, last):
    """Prevents rapid bouncing between duty levels."""
    if target >= last:
        return target  # heating up: respond immediately
    else:
        # cooling down: only decrease if temp is HYST below current threshold
        threshold = temp_threshold_for_duty(last)
        if t < threshold - HYST:
            return target
        else:
            return last


def set_fan(line_handle, duty):
    """Binary on/off control based on threshold (not true PWM)."""
    lgpio.gpio_write(line_handle, LINE, 1 if duty > 50 else 0)


# -------------------------------------------------------
# Main loop
# -------------------------------------------------------
def main():
    last_duty = 0
    h = lgpio.gpiochip_open(CHIP)
    lgpio.gpio_claim_output(h, LINE)

    try:
        while True:
            temp = get_cpu_temp()
            target = temp_to_duty(temp)
            duty = apply_hysteresis(temp, target, last_duty)
            last_duty = duty

            set_fan(h, duty)
            print(f"penta-fan: Temp={temp:.1f}°C, duty={duty}%")
            time.sleep(CHECK_INTERVAL)
    finally:
        lgpio.gpio_write(h, LINE, 0)
        lgpio.gpiochip_close(h)


if __name__ == "__main__":
    main()
