# ESP32-C3 Dev Module (tsuki-ex)

ESP32-C3 configurado para BLE-only. Arquitectura RISC-V a 80 MHz con WiFi desactivado por defecto para maximizar batería en proyectos BLE.

## Diferencias

| Parámetro | Estándar | tsuki-ex |
|---|---|---|
| WiFi | Habilitado | **Desactivado (CONFIG_ESP_WIFI_ENABLED=0)** |
| Bluetooth | BT+BLE | **BLE only (CONFIG_BTDM_CTRL_MODE_BLE_ONLY)** |
| CPU default | 160 MHz | **80 MHz** |
| Baud subida | 921600 | **2000000** |

## Activar WiFi si lo necesitas

Si el proyecto necesita WiFi, añade `CONFIG_ESP_WIFI_ENABLED=1` en los defines personalizados del proyecto. El paquete estándar `esp32c3` del registro principal no tiene esta restricción.
