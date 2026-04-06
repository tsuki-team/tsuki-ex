//! C FFI layer — symbols called from transpiled user sketch (C++)
//!
//! The tsuki transpiler converts user Go/Python sketches to C++ that includes
//! `tsuki_fw.h` and calls these functions. All symbols use the `tsuki_` prefix
//! and are declared `#[no_mangle] pub extern "C"`.
//!
//! See `include/tsuki_fw.h` for the matching C declarations.

use core::ffi::{c_char, c_int, c_uint, c_ulong};
use core::slice;
use core::str;

// ── System ────────────────────────────────────────────────────────────────────

/// Milliseconds since boot.
#[no_mangle]
pub extern "C" fn tsuki_millis() -> c_ulong {
    unsafe { esp_idf_sys::esp_timer_get_time() as c_ulong / 1000 }
}

/// Microseconds since boot.
#[no_mangle]
pub extern "C" fn tsuki_micros() -> c_ulong {
    unsafe { esp_idf_sys::esp_timer_get_time() as c_ulong }
}

/// Busy-wait for `ms` milliseconds (delegates to FreeRTOS delay).
#[no_mangle]
pub extern "C" fn tsuki_delay(ms: c_uint) {
    unsafe { esp_idf_sys::vTaskDelay(ms / portTICK_PERIOD_MS()) }
}

/// Enter deep sleep for `ms` milliseconds.
#[no_mangle]
pub extern "C" fn tsuki_sleep_ms(ms: c_ulong) {
    crate::hal::power::deep_sleep_ms(ms as u64);
}

fn portTICK_PERIOD_MS() -> c_uint {
    // 1000 / configTICK_RATE_HZ — usually 10 at 100 Hz
    (1000 / unsafe { esp_idf_sys::CONFIG_FREERTOS_HZ }) as c_uint
}

// ── Serial ────────────────────────────────────────────────────────────────────

/// Print a null-terminated string to UART0.
#[no_mangle]
pub extern "C" fn tsuki_print(s: *const c_char) {
    if s.is_null() { return; }
    let cstr = unsafe { core::ffi::CStr::from_ptr(s) };
    if let Ok(msg) = cstr.to_str() {
        log::info!("{msg}");
    }
}

/// Print a null-terminated string + newline.
#[no_mangle]
pub extern "C" fn tsuki_println(s: *const c_char) {
    tsuki_print(s);
}

// ── WiFi ──────────────────────────────────────────────────────────────────────

/// Connect to WiFi AP.
/// Returns 0 on success, -1 on error.
#[no_mangle]
#[cfg(feature = "wifi")]
pub extern "C" fn tsuki_wifi_connect(ssid: *const c_char, pass: *const c_char) -> c_int {
    let ssid = unsafe { core::ffi::CStr::from_ptr(ssid) }.to_str().unwrap_or("");
    let pass = unsafe { core::ffi::CStr::from_ptr(pass) }.to_str().unwrap_or("");
    match crate::modules::wifi::connect(ssid, pass) {
        Ok(_) => 0,
        Err(e) => { log::error!("wifi_connect err: {:?}", e); -1 }
    }
}

#[no_mangle]
#[cfg(not(feature = "wifi"))]
pub extern "C" fn tsuki_wifi_connect(_ssid: *const c_char, _pass: *const c_char) -> c_int {
    log::warn!("tsuki_wifi_connect: wifi module not enabled");
    -1
}

/// Disconnect from WiFi.
#[no_mangle]
pub extern "C" fn tsuki_wifi_disconnect() {
    #[cfg(feature = "wifi")]
    crate::modules::wifi::disconnect();
}

/// Returns 1 if WiFi is connected, 0 otherwise.
#[no_mangle]
pub extern "C" fn tsuki_wifi_connected() -> c_int {
    #[cfg(feature = "wifi")]
    return crate::modules::wifi::is_connected() as c_int;
    #[cfg(not(feature = "wifi"))]
    return 0;
}

// ── Bluetooth / BLE ───────────────────────────────────────────────────────────

/// Start BLE advertising with the given device name.
#[no_mangle]
#[cfg(feature = "bluetooth")]
pub extern "C" fn tsuki_ble_advertise(name: *const c_char) -> c_int {
    let name = unsafe { core::ffi::CStr::from_ptr(name) }.to_str().unwrap_or("tsuki");
    match crate::modules::bt::advertise(name) {
        Ok(_) => 0,
        Err(e) => { log::error!("ble_advertise err: {:?}", e); -1 }
    }
}

#[no_mangle]
#[cfg(not(feature = "bluetooth"))]
pub extern "C" fn tsuki_ble_advertise(_name: *const c_char) -> c_int {
    log::warn!("tsuki_ble_advertise: bluetooth module not enabled");
    -1
}

/// Stop BLE advertising.
#[no_mangle]
pub extern "C" fn tsuki_ble_stop() {
    #[cfg(feature = "bluetooth")]
    crate::modules::bt::stop_advertise();
}

// ── Filesystem ────────────────────────────────────────────────────────────────

/// Write `len` bytes from `data` to `path` (relative to /spiffs/).
/// Returns 0 on success, -1 on error.
#[no_mangle]
#[cfg(feature = "filesystem")]
pub extern "C" fn tsuki_fs_write(
    path: *const c_char,
    data: *const u8,
    len: c_uint,
) -> c_int {
    let path = unsafe { core::ffi::CStr::from_ptr(path) }.to_str().unwrap_or("");
    let data = unsafe { slice::from_raw_parts(data, len as usize) };
    match crate::modules::fs::write_file(path, data) {
        Ok(_) => 0,
        Err(e) => { log::error!("fs_write: {e}"); -1 }
    }
}

#[no_mangle]
#[cfg(not(feature = "filesystem"))]
pub extern "C" fn tsuki_fs_write(
    _path: *const c_char,
    _data: *const u8,
    _len: c_uint,
) -> c_int {
    log::warn!("tsuki_fs_write: filesystem module not enabled");
    -1
}

/// Read file at `path` into `buf` (max `buf_len` bytes).
/// Returns number of bytes read, or -1 on error.
#[no_mangle]
#[cfg(feature = "filesystem")]
pub extern "C" fn tsuki_fs_read(
    path: *const c_char,
    buf: *mut u8,
    buf_len: c_uint,
) -> c_int {
    let path = unsafe { core::ffi::CStr::from_ptr(path) }.to_str().unwrap_or("");
    match crate::modules::fs::read_file(path) {
        Ok(data) => {
            let n = data.len().min(buf_len as usize);
            unsafe { slice::from_raw_parts_mut(buf, n) }.copy_from_slice(&data[..n]);
            n as c_int
        }
        Err(e) => { log::error!("fs_read: {e}"); -1 }
    }
}

#[no_mangle]
#[cfg(not(feature = "filesystem"))]
pub extern "C" fn tsuki_fs_read(
    _path: *const c_char,
    _buf: *mut u8,
    _buf_len: c_uint,
) -> c_int {
    -1
}

/// Delete file at `path`.
#[no_mangle]
pub extern "C" fn tsuki_fs_delete(path: *const c_char) -> c_int {
    #[cfg(feature = "filesystem")]
    {
        let path = unsafe { core::ffi::CStr::from_ptr(path) }.to_str().unwrap_or("");
        match crate::modules::fs::delete_file(path) {
            Ok(_) => 0,
            Err(e) => { log::error!("fs_delete: {e}"); -1 }
        }
    }
    #[cfg(not(feature = "filesystem"))]
    return -1;
}
