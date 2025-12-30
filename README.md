# Radxa Penta SATA HAT — Pi 5 Fan Fix

Temperature-based fan control for the Radxa Penta SATA HAT on Raspberry Pi 5, using `lgpio` and a simple Python script.

## Problem

The Radxa `rockpi-penta` package was written for Raspberry Pi 4 and `libgpiod` v1.  
Raspberry Pi OS for Pi 5 ships with `libgpiod` v2, which has an incompatible API. This can cause:

- Fan control service to crash or fail silently  
- Fan to run at full speed constantly  
- OLED display to fail to initialize

## Solution

This repository replaces Radxa’s fan control with a standalone Python script that:

- Uses `lgpio` (the Raspberry Pi–supported GPIO library)
- Drives the fan using hardware PWM
- Sets fan speed based on CPU temperature
- Cleanly turns the fan off when the service stops

The OLED can be left alone or handled separately (see `OLED.md` if you want to integrate it).

---

## Installation

### 1. Install dependencies

```bash
sudo apt update
sudo apt install python3-lgpio
```

### 2. Install the fan control script

```bash
sudo cp penta_fan.py /usr/local/bin/
sudo chmod +x /usr/local/bin/penta_fan.py
```

### 3. Install and enable the systemd service

```bash
sudo cp penta-fan.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now penta-fan.service
```

### 4. Verify the service

```bash
systemctl status penta-fan.service
```

You should see `Active: active (running)`.

To watch temperature and duty updates:

```bash
sudo journalctl -u penta-fan.service -f
```

Example log output:

```text
penta-fan: Temp=51.2°C, duty=45%
penta-fan: Temp=55.0°C, duty=70%
```

---

## Configuration

The fan behaviour is controlled in `penta_fan.py`.

### Fan curve

The default temperature–duty mapping is:

```python
def temp_to_duty(t):
    """
    Map CPU temperature (°C) to fan duty (%).
    Adjust thresholds and levels to taste.
    """
    if t < 45:
        return 0        # off
    elif t < 50:
        return 30       # gentle
    elif t < 55:
        return 45
    elif t < 60:
        return 70
    else:
        return 100      # full speed when hot
```

You can change the thresholds and duty values to make the fan quieter or more aggressive. After any changes:

```bash
sudo systemctl restart penta-fan.service
```

### GPIO mapping and PWM

At the top of `penta_fan.py`:

```python
CHIP = 0          # gpiochip0
LINE = 27         # fan control pin
PWM_FREQ = 100    # PWM frequency in Hz
```

These values are:

- **CHIP 0 / LINE 27** – GPIO line used by the fan control pin in this setup  
- **PWM_FREQ = 100 Hz** – a frequency that works reliably with `lgpio` on Pi 5 for this fan

If your hardware revision or wiring differ and the fan does not respond, you may need to adjust `CHIP` and `LINE` to match your configuration.

---

## OLED Display (Optional)

This setup focuses on fan control.  
If you want the OLED display from the Radxa Penta SATA HAT to work alongside this fix, see `OLED.md` for notes on adapting or stubbing the original `rockpi-penta` package.

---

## Hardware

Tested with:

- Raspberry Pi 5 (8 GB)
- Radxa Penta SATA HAT
- Raspberry Pi OS (64-bit) with kernel 6.12
- Fan control line on `gpiochip0`, line 27

---

## License

MIT
