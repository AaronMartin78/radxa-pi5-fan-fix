# OLED Display Setup (Optional)

The Radxa `rockpi-penta` package can still drive the OLED display on Pi 5, but the fan and button code must be disabled to prevent crashes.

## Prerequisites

- The `rockpi-penta` package installed (from Radxa's repo or built from source)
- `penta-fan.service` from this repo handling fan control

## Steps

### 1. Stub out the fan code

Append this to the end of `/usr/bin/rockpi-penta/fan.py`:

```python
# ---- Pi 5 compatibility stub (override legacy fan code) ----
def running(*args, **kwargs):
    import time
    try:
        print("gpiod v2 detected on Pi 5, disabling rockpi-penta fan thread.")
    except Exception:
        pass
    while True:
        time.sleep(5)
```

Python uses the last definition, so this overrides the earlier `running()` function.

### 2. Stub out the button code

Append this to the end of `/usr/bin/rockpi-penta/misc.py`:

```python
# ---- Pi 5 compatibility stubs (override legacy gpiod v1 button code) ----
def read_key(pattern, size):
    return None

def watch_key(pattern=None, size=None, q=None):
    return
```

### 3. Restart the service

```bash
sudo systemctl restart rockpi-penta.service
```

### 4. Verify I2C

The OLED should appear at address `0x3c`:

```bash
i2cdetect -y 1
```

## Configuration

Edit `/etc/rockpi-penta.conf` to customize display behavior:

```ini
[fan]
lv0 = 35
lv1 = 40
lv2 = 45
lv3 = 50

[key]
click = slider
twice = switch
press = none

[time]
twice = 0.7
press = 1.8

[slider]
auto = true
time = 8

[oled]
enable = 1
rotate = false
f-temp = false
```

Note: The `[fan]` and `[key]` sections are ignored when using our stubs, but the config parser still expects them.

## Result

- `penta-fan.service` — controls the fan (this repo)
- `rockpi-penta.service` — drives the OLED only (fan/button threads disabled)
