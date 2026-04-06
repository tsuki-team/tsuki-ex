/**
 * tsuki_fw.h — C/C++ interface to the tsuki-ex firmware
 *
 * Included automatically by the tsuki transpiler when it outputs C++
 * from a user sketch that targets an ESP32 board package from tsuki-ex.
 *
 * All symbols are implemented in Rust (src/ffi.rs) and linked via LTO.
 *
 * Usage in generated sketch.cpp:
 *   #include "tsuki_fw.h"
 *   void tsuki_user_setup() { ... }
 *   void tsuki_user_loop()  { ... }
 */

#pragma once

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ── System ──────────────────────────────────────────────────────────────── */

/** Milliseconds since boot. */
unsigned long tsuki_millis(void);

/** Microseconds since boot. */
unsigned long tsuki_micros(void);

/** Block for `ms` milliseconds (FreeRTOS vTaskDelay). */
void tsuki_delay(unsigned int ms);

/** Enter deep sleep for `ms` milliseconds, then wake via timer. */
void tsuki_sleep_ms(unsigned long ms);

/* ── Serial / Logging ────────────────────────────────────────────────────── */

void tsuki_print(const char *s);
void tsuki_println(const char *s);

/* ── WiFi ────────────────────────────────────────────────────────────────── */

/**
 * Connect to a WiFi AP.
 * Activates the WiFi module; enters modem sleep after tsuki_wifi_disconnect().
 * Returns 0 on success, -1 on error.
 *
 * Only available when compiled with feature = "wifi"
 * (set automatically when // #[modules(Wifi)] is present in user source).
 */
int tsuki_wifi_connect(const char *ssid, const char *password);

/** Disconnect and power down WiFi modem. */
void tsuki_wifi_disconnect(void);

/** Returns 1 if currently connected, 0 otherwise. */
int tsuki_wifi_connected(void);

/* ── Bluetooth / BLE ─────────────────────────────────────────────────────── */

/**
 * Start BLE advertising with the given device name.
 * Returns 0 on success, -1 on error.
 *
 * Only available when compiled with feature = "bluetooth"
 * (set automatically when // #[modules(Bt)] or // #[modules(Ble)] present).
 */
int tsuki_ble_advertise(const char *name);

/** Stop BLE advertising. */
void tsuki_ble_stop(void);

/* ── Filesystem (SPIFFS) ─────────────────────────────────────────────────── */

/**
 * Write `len` bytes from `data` to a file at `path` (relative to /spiffs/).
 * Creates the file if it does not exist; overwrites if it does.
 * Returns 0 on success, -1 on error.
 *
 * Only available when compiled with feature = "filesystem"
 * (set automatically when // #[modules(Fs)] is present in user source).
 */
int tsuki_fs_write(const char *path, const uint8_t *data, unsigned int len);

/**
 * Read file at `path` into `buf` (at most `buf_len` bytes).
 * Returns number of bytes read, or -1 on error.
 */
int tsuki_fs_read(const char *path, uint8_t *buf, unsigned int buf_len);

/**
 * Delete file at `path`.
 * Returns 0 on success, -1 on error.
 */
int tsuki_fs_delete(const char *path);

/* ── User sketch hooks (defined by transpiled C++) ───────────────────────── */

/**
 * These are implemented by the transpiler output, called by the Rust runtime.
 * Do NOT call them directly.
 */
void tsuki_user_setup(void);
void tsuki_user_loop(void);

#ifdef __cplusplus
} /* extern "C" */
#endif


/* ═══════════════════════════════════════════════════════════════════════════
 * Convenience macros for generated code
 * ═══════════════════════════════════════════════════════════════════════════ */

/** Print a string literal. */
#define TSUKI_PRINT(s)    tsuki_print(s)
#define TSUKI_PRINTLN(s)  tsuki_println(s)

/** Delay in milliseconds. */
#define TSUKI_DELAY(ms)   tsuki_delay(ms)
