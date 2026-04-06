# tsuki-ex firmware

Rust firmware for ESP32 family boards, designed to work with the tsuki IDE and CLI.

## How it works

The tsuki transpiler converts user sketches (Go/Python) to C++. When the target board is from the `tsuki-ex` registry, the transpiler:

1. Includes `tsuki_fw.h` in the generated C++
2. Emits `TSUKI_FLAGS` and `TSUKI_MODULES` environment variables before calling `cargo build`
3. Links the compiled Rust firmware with the generated C++ object

The Rust runtime calls `tsuki_user_setup()` once, then `tsuki_user_loop()` forever.

---

## Annotations in user source

### `// #[flags(...)]`

Set numeric constants readable by the firmware:

```go
// #[flags("UPLOAD=20000", "MODE=2", "BAUD=115200")]
func setup() {
  // ...
}
```

| Flag     | Effect                                               | Default |
|----------|------------------------------------------------------|---------|
| `UPLOAD` | Flash upload baud rate                               | 2000000 |
| `BAUD`   | Serial monitor baud rate                             | 115200  |
| `MODE`   | Power mode: 0=normal, 1=low-power, 2=ultra-low-power | 0       |

Custom flags become `FLAG_<NAME>` constants in the generated firmware.

### `// #[modules(...)]`

Activate optional hardware modules:

```go
// #[modules(Wifi, Fs)]
func setup() {
  wifi_connect("MyNetwork", "password")
  fs_write("data.txt", "hello")
}
```

| Module     | Cargo feature | What it enables                          |
|------------|---------------|------------------------------------------|
| `Wifi`     | `wifi`        | WiFi station mode + modem sleep on idle  |
| `Bt`/`Ble` | `bluetooth`   | BLE advertising and GATT (BLE-only mode) |
| `Fs`       | `filesystem`  | SPIFFS flash filesystem at `/spiffs`     |

Modules not listed are compiled out entirely — zero ROM/RAM overhead.

---

## Building manually

```sh
# Install Espressif Rust toolchain once
cargo install espup && espup install

# Build with WiFi + filesystem
TSUKI_MODULES="Wifi,Fs" TSUKI_FLAGS="MODE=1" cargo build --release

# Flash
espflash flash --monitor target/xtensa-esp32-espidf/release/tsuki-ex-fw
```

---

## Filesystem

When `Fs` is active, a SPIFFS partition (`storage`, 896 KB) is mounted at `/spiffs`.

FFI functions: `tsuki_fs_write`, `tsuki_fs_read`, `tsuki_fs_delete`.

Partition layout: see `partitions.csv`.

---

## Power modes

| MODE | CPU        | Sleep             |
|------|------------|-------------------|
| 0    | 240 MHz    | none              |
| 1    | 80 MHz     | light sleep idle  |
| 2    | 80 MHz     | deep sleep capable|

`tsuki_sleep_ms(ms)` triggers a timed deep sleep from user code.
