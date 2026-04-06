//! Power management helpers
//!
//! Maps POWER_MODE (from TSUKI_FLAGS="MODE=N") to ESP-IDF pm config.
//! MODE=0 → default (240 MHz, no pm)
//! MODE=1 → low-power   (80 MHz, automatic light sleep)
//! MODE=2 → ultra-low   (80 MHz, automatic deep sleep between loops)

use esp_idf_sys::{
    esp_pm_config_esp32_t,
    esp_pm_configure,
    esp_sleep_enable_timer_wakeup,
    esp_deep_sleep_start,
};

pub fn set_low_power() {
    unsafe {
        let cfg = esp_pm_config_esp32_t {
            max_freq_mhz: 80,
            min_freq_mhz: 40,
            light_sleep_enable: true,
        };
        esp_pm_configure(&cfg as *const _ as *const _);
    }
    log::info!("power: low-power mode (80 MHz + light sleep)");
}

pub fn set_ultra_low_power() {
    unsafe {
        let cfg = esp_pm_config_esp32_t {
            max_freq_mhz: 80,
            min_freq_mhz: 20,
            light_sleep_enable: true,
        };
        esp_pm_configure(&cfg as *const _ as *const _);
    }
    log::info!("power: ultra-low-power mode (80 MHz, deep-sleep capable)");
}

/// Enter deep sleep for `ms` milliseconds, then wake automatically.
/// Used by tsuki_sleep_ms() FFI call.
pub fn deep_sleep_ms(ms: u64) {
    unsafe {
        esp_sleep_enable_timer_wakeup(ms * 1000); // µs
        esp_deep_sleep_start();
    }
}
