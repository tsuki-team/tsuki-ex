//! Flash filesystem module — feature = "filesystem"
//!
//! Mounts a SPIFFS partition labelled "storage" (see partitions.csv).
//! Exposed to user sketches via tsuki_fs_* FFI functions.
//!
//! Activation in tsuki source:
//!   // #[modules(Fs)]
//!
//! After mounting, files are accessible at the standard VFS path "/spiffs".

use esp_idf_sys::{
    esp,
    esp_vfs_spiffs_conf_t,
    esp_vfs_spiffs_register,
    esp_vfs_spiffs_unregister,
    EspError,
};
use std::ffi::CStr;

const BASE_PATH: &[u8] = b"/spiffs\0";
const PARTITION_LABEL: &[u8] = b"storage\0";
const MAX_FILES: usize = 5;

static mut MOUNTED: bool = false;

pub fn init() -> Result<(), EspError> {
    unsafe {
        if MOUNTED {
            return Ok(());
        }

        let conf = esp_vfs_spiffs_conf_t {
            base_path: BASE_PATH.as_ptr() as *const _,
            partition_label: PARTITION_LABEL.as_ptr() as *const _,
            max_files: MAX_FILES as _,
            format_if_mount_failed: true,
        };

        esp!(esp_vfs_spiffs_register(&conf))?;
        MOUNTED = true;
        log::info!("fs: SPIFFS mounted at /spiffs");
    }
    Ok(())
}

pub fn deinit() {
    unsafe {
        if MOUNTED {
            esp_vfs_spiffs_unregister(PARTITION_LABEL.as_ptr() as *const _);
            MOUNTED = false;
            log::info!("fs: SPIFFS unmounted");
        }
    }
}

/// Write bytes to a file (creates or overwrites).
pub fn write_file(path: &str, data: &[u8]) -> Result<(), &'static str> {
    use std::fs::File;
    use std::io::Write;
    let full = format!("/spiffs/{path}");
    let mut f = File::create(&full).map_err(|_| "fs: create failed")?;
    f.write_all(data).map_err(|_| "fs: write failed")
}

/// Read entire file into a Vec<u8>.
pub fn read_file(path: &str) -> Result<alloc::vec::Vec<u8>, &'static str> {
    use std::fs::File;
    use std::io::Read;
    let full = format!("/spiffs/{path}");
    let mut f = File::open(&full).map_err(|_| "fs: open failed")?;
    let mut buf = alloc::vec::Vec::new();
    f.read_to_end(&mut buf).map_err(|_| "fs: read failed")?;
    Ok(buf)
}

/// Delete a file.
pub fn delete_file(path: &str) -> Result<(), &'static str> {
    let full = format!("/spiffs/{path}");
    std::fs::remove_file(&full).map_err(|_| "fs: delete failed")
}
