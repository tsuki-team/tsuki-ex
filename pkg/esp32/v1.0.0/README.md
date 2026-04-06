# ESP32 Dev Module (tsuki-ex)

Versión optimizada del ESP32 con foco en tamaño de firmware, velocidad de subida y consumo energético.

## Diferencias frente al paquete estándar

| Parámetro | Estándar | tsuki-ex |
|---|---|---|
| Frecuencia CPU | 240 MHz | **80 MHz** |
| Bluetooth | Habilitado | **Deshabilitado** (-100 KB flash) |
| Modo sleep WiFi | Manual | **Modem sleep automático** |
| Baud subida | 921600 | **2000000** (~2× más rápido) |
| Gestión de energía | Desactivada | **CONFIG_PM_ENABLE=1** |

## Tamaño de binario típico

| Proyecto | Estándar | tsuki-ex |
|---|---|---|
| Blink | 860 KB | ~420 KB |
| WiFi HTTP GET | 1.1 MB | ~680 KB |
| MQTT client | 1.4 MB | ~890 KB |

## WiFi bajo demanda

El radio WiFi arranca **apagado**. Solo se activa cuando el código lo solicita:

```go
import (
    "arduino"
    "wifi"
)

func setup() {
    arduino.Serial.Begin(115200)
    // Radio OFF — consumo base ~20 mA
}

func loop() {
    // Activa WiFi solo cuando hace falta
    wifi.Connect("SSID", "password")
    resp := http.Get("https://api.example.com/data")
    wifi.Disconnect()  // radio vuelve a modem sleep

    arduino.Delay(30000)  // 30 s dormido: ~2 mA
}
```

## Detectar tsuki-ex en tiempo de compilación

```go
// main.go — con bloque C inline (tsuki soporta `// #ifdef`)
func setup() {
    // #ifdef TSUKI_EX
    arduino.Serial.Println("Firmware tsuki-ex activo")
    // #endif
}
```

## Notas

- Si necesitas Bluetooth, usa el paquete `esp32` del registro estándar.
- La frecuencia de 80 MHz es perfectamente suficiente para la mayoría de proyectos WiFi.
- Para proyectos de ultra bajo consumo, combina con `esp_deep_sleep_start()` en C inline.
