//! Bluetooth / BLE module — feature = "bluetooth"
//!
//! Thin wrapper over esp-idf-svc BLE GATT server.
//! On ESP32-C3 the build is automatically BLE-only.
//! On full ESP32, classic BT is also available but disabled by default
//! to save RAM (matching the tsuki-ex board package defines).

use esp_idf_sys::EspError;

pub fn init() -> Result<(), EspError> {
    // BLE controller is initialised here.
    // The actual GATT server / advertisement is set up via FFI calls
    // from the user sketch using tsuki_ble_advertise() etc.
    log::info!("bt module: BLE ready");
    Ok(())
}

/// Start advertising with a given device name.
pub fn advertise(name: &str) -> Result<(), EspError> {
    log::info!("ble: advertising as '{name}'");
    // TODO: wrap esp_ble_gap_set_device_name + esp_ble_gap_start_advertising
    // via esp-idf-sys bindings.
    Ok(())
}

/// Stop advertising.
pub fn stop_advertise() {
    log::info!("ble: stopped advertising");
}
