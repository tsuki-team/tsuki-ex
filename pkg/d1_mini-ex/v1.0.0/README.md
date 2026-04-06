# Wemos D1 Mini (tsuki-ex)

D1 Mini con modem sleep y binario reducido. Igual que el `esp8266` ex pero con el FQBN específico del D1 Mini.

## Diferencias

| Parámetro | Estándar | tsuki-ex |
|---|---|---|
| Baud subida | 921600 | **2000000** |
| lwIP | Completo | **Reducido** |
| Modem sleep | Manual | **Entre transmisiones** |
| Binario típico | ~380 KB | ~235 KB |
