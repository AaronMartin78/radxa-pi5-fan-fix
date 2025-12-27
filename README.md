# Radxa Penta SATA HAT — Pi 5 Fan Fix

Temperature-based fan control for the Radxa Penta SATA HAT on Raspberry Pi 5.

## Problem

The Radxa `rockpi-penta` package was written for Raspberry Pi 4 and uses gpiod v1. Raspberry Pi OS on Pi 5 ships with gpiod v2, which has an incompatible API. This causes:

- Fan control service crashes or fails silently
- Fan runs at full speed constantly
- OLED display fails to initialize

## Solution

Replace Radxa's fan control with a custom script using `lgpio`, the official Pi 5 GPIO library. Optionally keep the OLED working by stubbing out the broken gpiod v1 calls in the original package.

## Installation

### 1. Install lgpio

```bash
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

### 4. Verify

```bash
systemctl status penta-fan.service
```

The fan should now run quietly and spin up only when CPU temperature rises.

## Configuration

Edit `/usr/local/bin/penta_fan.py` to adjust the fan curve:

```python
def temp_to_duty(t):
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
        return 100    # full power
```

Note: The Radxa HAT fan pin is binary (on/off), not true PWM. The fan turns on when duty exceeds 50%.

Restart after changes:

```bash
sudo systemctl restart penta-fan.service
```

## OLED Display (Optional)

If you want the OLED to work alongside this fix, see [OLED.md](OLED.md).

## Hardware

Tested with:
- Raspberry Pi 5 (8 GB)
- Radxa Penta SATA HAT (fan on BCM GPIO 27)
- Raspberry Pi OS (64-bit), kernel 6.12

## License

MIT
