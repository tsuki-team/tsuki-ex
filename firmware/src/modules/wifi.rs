//! WiFi module — feature = "wifi"
//!
//! Manages a single station-mode connection.
//! The firmware keeps WiFi OFF until the user sketch calls `tsuki_wifi_connect()`.
//! After `tsuki_wifi_disconnect()` it enters modem sleep automatically.

use esp_idf_svc::{
    eventloop::EspSystemEventLoop,
    nvs::EspDefaultNvsPartition,
    wifi::{BlockingWifi, ClientConfiguration, Configuration, EspWifi},
};
use esp_idf_hal::peripheral::Peripheral;
use esp_idf_sys::EspError;
use std::sync::Mutex;

static WIFI: Mutex<Option<BlockingWifi<EspWifi<'static>>>> = Mutex::new(None);

pub fn init() -> Result<(), EspError> {
    // WiFi driver is created lazily on first connect call.
    log::info!("wifi module: ready (lazy init)");
    Ok(())
}

/// Connect to an AP.  Called from FFI `tsuki_wifi_connect(ssid, pass)`.
pub fn connect(ssid: &str, password: &str) -> Result<(), EspError> {
    let sysloop = EspSystemEventLoop::take()?;
    let nvs = EspDefaultNvsPartition::take()?;

    // Safety: we hold the mutex for the entire duration
    let modem = unsafe { esp_idf_hal::modem::WifiModem::new() };
    let inner = EspWifi::new(modem, sysloop.clone(), Some(nvs))?;
    let mut wifi = BlockingWifi::wrap(inner, sysloop)?;

    wifi.set_configuration(&Configuration::Client(ClientConfiguration {
        ssid: heapless::String::try_from(ssid).unwrap_or_default(),
        password: heapless::String::try_from(password).unwrap_or_default(),
        ..Default::default()
    }))?;

    wifi.start()?;
    wifi.connect()?;
    wifi.wait_netif_up()?;

    log::info!("wifi: connected to {ssid}");
    *WIFI.lock().unwrap() = Some(wifi);
    Ok(())
}

/// Disconnect and power down modem.
pub fn disconnect() {
    if let Ok(mut guard) = WIFI.lock() {
        if let Some(mut w) = guard.take() {
            let _ = w.disconnect();
            let _ = w.stop();
        }
    }
    log::info!("wifi: disconnected, modem sleep");
}

/// Returns true if currently connected.
pub fn is_connected() -> bool {
    WIFI.lock()
        .ok()
        .and_then(|g| g.as_ref().map(|w| w.is_connected().unwrap_or(false)))
        .unwrap_or(false)
}
