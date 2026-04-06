# ESP8266 Generic (tsuki-ex)

ESP8266 con modem sleep activado por defecto y binarios más pequeños.

## Diferencias frente al paquete estándar

| Parámetro | Estándar | tsuki-ex |
|---|---|---|
| Baud subida | 921600 | **2000000** |
| Modem sleep | Manual | **Automático entre transmisiones** |
| lwIP features | Completo | **Reducido (LWIP_FEATURES=0)** |
| Tamaño binario típico | ~380 KB | ~240 KB |

## Consumo energético

Con modem sleep y `wifi.Disconnect()` entre ciclos:

| Estado | Consumo |
|---|---|
| WiFi activo, transmitiendo | ~170 mA |
| Modem sleep (radio off) | ~15 mA |
| Deep sleep (requiere C inline) | ~20 µA |

## Notas

- `LWIP_FEATURES=0` desactiva IPv6 y mDNS — suficiente para la mayoría de proyectos IoT.
- Compatible con todos los módulos ESP8266: ESP-12E, ESP-12F, ESP-01S.
