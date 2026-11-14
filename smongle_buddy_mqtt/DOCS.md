# Home Assistant Add-on: Smongle Buddy MQTT

Dieses Add-on liest die Messdaten des **Smongle(r) Buddy** (von mechsat e.U.) über die USB-Serial-Schnittstelle aus und veröffentlicht sie per MQTT inklusive Home Assistant Auto-Discovery.

## Installation & Einrichtung

1. Schließe den Smongle(r) Buddy per USB an deinen Home Assistant Host an.
2. Ermittle unter **Einstellungen → System → Hardware → Gesamte Hardware** den genauen seriellen Pfad (z. B. `/dev/ttyACM0` oder `/dev/ttyUSB0`).
3. Trage den Pfad sowie deine MQTT-Zugangsdaten im Reiter **Konfiguration** ein.
4. Starte das Add-on und aktiviere bei Bedarf **Bei Systemstart starten**.

## Konfiguration

Beispielkonfiguration:

```yaml
mqtt_host: "core-mosquitto"
mqtt_port: 1883
mqtt_username: "mqtt_user"
mqtt_password: "dein_passwort"
serial_device: "/dev/ttyACM0"
operation_mode: "Automatik (PUSH)"
poll_interval: 5