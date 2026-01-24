#!/usr/bin/env python3***
import time
import lgpio

# -------------------------------------------------------
# CONFIG
# -------------------------------------------------------

# These are confirmed working for your Radxa Penta SATA HAT fan on Pi 5
CHIP = 0               # gpiochip0
LINE = 27              # fan PWM line (from gpioinfo: FAN_PWM)

PWM_FREQ = 100         # 10kHz (highest supported on this line)
CHECK_INTERVAL = 2.0   # seconds between temperature checks


# -------------------------------------------------------
# HELPERS
# -------------------------------------------------------

def get_cpu_temp():
    """Read CPU temperature in °C from the kernel."""
    with open("/sys/class/thermal/thermal_zone0/temp") as f:
        return int(f.read().strip()) / 1000.0


def temp_to_duty(t):
    """
    Map temperature (°C) to fan duty (%).

    This curve starts the fan early so it's easy to SEE/HEAR that it's working.
    You can tune the thresholds and duty steps later if you want it quieter.
    """
    if t < 56.0:
        return 0        # cold: off
    elif t < 58.0:
        return 30       # gentle
    elif t < 60.0:
        return 45
    elif t < 63.0:
        return 70
    else:
        return 100      # hot: full blast


def set_fan(handle, duty):
    """
    Set fan speed via hardware PWM.
    Kick with brief pulse first to ensure PWM takes control.
    """
    duty = max(0, min(100, int(duty)))
    # Brief kick to ensure PWM is active on the line
    lgpio.tx_pwm(handle, LINE, PWM_FREQ, 1)
    time.sleep(0.05)
    # Now set actual duty
    if duty == 0:
        lgpio.tx_pwm(handle, LINE, PWM_FREQ, 0)
        lgpio.gpio_write(handle, LINE, 0)
    else:
        lgpio.tx_pwm(handle, LINE, PWM_FREQ, duty)

# -------------------------------------------------------
# MAIN LOOP
# -------------------------------------------------------

def main():
    h = lgpio.gpiochip_open(CHIP)
    lgpio.gpio_claim_output(h, LINE)
    
    # Initialize PWM control by briefly asserting it
    lgpio.tx_pwm(h, LINE, PWM_FREQ, 100)
    time.sleep(0.5)


    last_duty = None

    FAN_ON_TEMP  = 56.0
    FAN_OFF_TEMP = 54.0
    fan_enabled = False

    try:
        while True:
            temp = get_cpu_temp()

            # hysteresis gate
            if fan_enabled:
                if temp <= FAN_OFF_TEMP:
                    fan_enabled = False
            else:
                if temp >= FAN_ON_TEMP:
                    fan_enabled = True

            duty = temp_to_duty(temp) if fan_enabled else 0

            # Always log temp + duty so behaviour is visible in journalctl
            print(f"penta-fan: Temp={temp:.1f}°C, duty={duty}%")

            if duty != last_duty:
                set_fan(h, duty)
                last_duty = duty

            time.sleep(CHECK_INTERVAL)
    finally:
        # On exit (Ctrl+C, systemd stop), make sure the fan is turned off
        try:
            set_fan(h, 0)
        except Exception:
            lgpio.gpio_write(h, LINE, 0)
        lgpio.gpiochip_close(h)


if __name__ == "__main__":
    main()
