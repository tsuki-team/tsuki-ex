# tsuki-ex

Optimized board packages for [tsuki](https://github.com/tsuki-team/tsuki). Drop-in replacements for standard board packages — same IDs, smarter defaults.

## What's different

| Feature | Standard | tsuki-ex |
|---|---|---|
| CPU freq (ESP32) | 240 MHz | 80 MHz default |
| WiFi radio | Always on | On-demand only |
| Bluetooth | Enabled | Disabled (saves ~100 KB flash) |
| Upload baud | 921600 | 2000000 |
| Compiler | `-O2` | `-Os` (size-optimized) |
| Binary size | ~850 KB | ~420 KB typical |

## Quick start

Add this registry URL in tsuki settings (Packages → Registries) or via CLI:

```
https://raw.githubusercontent.com/tsuki-team/tsuki-ex/refs/heads/main/pkg/packages.json
```

Or with the CLI:

```bash
tsuki config registry add https://raw.githubusercontent.com/tsuki-team/tsuki-ex/refs/heads/main/pkg/packages.json
```

The tsuki-ex registry has higher priority than the built-in one, so its board packages override the defaults automatically.

Then install a board:

```bash
tsuki boards install esp32
```

## Available packages

| ID | Board | Arch | Key changes |
|---|---|---|---|
| `esp32` | ESP32 Dev Module | esp32 | 80 MHz, no BT, WiFi on-demand |
| `esp8266` | ESP8266 Generic | esp8266 | modem sleep, -Os |
| `esp32s2` | ESP32-S2 Dev Module | esp32 | LP core, 80 MHz |
| `esp32c3` | ESP32-C3 Dev Module | esp32 | BLE-only mode, 80 MHz |
| `d1_mini` | Wemos D1 Mini | esp8266 | modem sleep, -Os, 2 Mbaud |

## WiFi on-demand pattern

tsuki-ex boards keep the radio off at boot. Enable it when needed:

```go
import (
    "arduino"
    "wifi"
)

func setup() {
    arduino.Serial.Begin(115200)
    // Radio is OFF here — zero power draw
}

func loop() {
    // Enable WiFi only when needed
    wifi.Connect("MySSID", "password")
    // ... do network work ...
    wifi.Disconnect()  // radio goes back to sleep
    arduino.Delay(30000)
}
```

## Detecting tsuki-ex at compile time

```go
// main.go
import "arduino"

func setup() {
    // #ifdef TSUKI_EX
    arduino.Serial.Println("Running on tsuki-ex firmware")
    // #endif
}
```

## Contributing

Board packages live in `pkg/<id>/v<version>/`. Each package contains:

- `tsuki_board.toml` — board manifest
- `sandbox.json` — circuit sandbox pin layout
- `ports.json` — USB auto-detection rules
- `README.md` — board-specific notes

To sync `packages.json` after adding or modifying a package:

```bash
python tools/pkg_manager.py sync
```

## License

MIT
