# ESP32-S2 Dev Module (tsuki-ex)

ESP32-S2 con LP core habilitado y 80 MHz por defecto. El S2 no tiene Bluetooth, lo que lo hace ideal para WiFi de bajo consumo.

## Diferencias

| Parámetro | Estándar | tsuki-ex |
|---|---|---|
| CPU default | 240 MHz | **80 MHz** |
| LP (ULP) core | Desactivado | **Habilitado (CONFIG_ULP_COPROC_ENABLED)** |
| Gestión de energía | Off | **CONFIG_PM_ENABLE=1** |
| Baud subida | 921600 | **2000000** |

## LP core

El co-procesador de ultra bajo consumo (ULP) puede ejecutar código simple mientras el núcleo principal duerme. Útil para lectura periódica de sensores sin despertar el CPU principal.
