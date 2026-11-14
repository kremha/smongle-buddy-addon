# Smongle Buddy MQTT

Lokales Home-Assistant-App/Add-on für den Smongle Buddy.

- USB-Serial mit 115200 Baud
- fragt den Buddy mit `api` ab
- veröffentlicht das vollständige JSON retained unter `smongle_buddy/data`
- erstellt MQTT-Discovery-Sensoren für ausgewählte skalare Messwerte

Nach dem Kopieren nach `/addons/smongle_buddy_mqtt` in Home Assistant unter **Einstellungen → Apps → App-Store → ⋮ → Nach Updates suchen** die lokale App installieren.
