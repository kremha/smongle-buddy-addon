# Changelog - Smongle Buddy MQTT

## [0.1.4| - 2026-11-14
- OPERATION_MODE definiert, Logging erweitert
- Automatik (PUSH): Lauscht kontinuierlich im Hintergrund auf ankommende Zeilen, ohne künstliche Timeouts oder aktive Abfragen.
- Manuell (PULL): Sendet im eingestellten Intervall das api-Kommando und liest die Antwort ein.

## [0.1.2] - 2026-11-14
- MQTT Userdaten als Eingabefelder
- USB Port als Eingabefeld
- Translation: DE
- Icon hinzugefügt

## [0.1.1] - 2026-11-14
- Herstellername auf "mechsat e.U." korrigiert.
- Konfigurationsoption für Betriebsmodus ("Automatik (PUSH)" vs. "Manuell (PULL)") hinzugefügt.
- Manuelles Abfrageintervall (1 bis 15 Minuten) in der Konfiguration wählbar gemacht.
- Entitätsnamen bereinigt und Umlaute durch ae, oe, ue ersetzt.

## [0.1.0] - Initiale Version
- USB-Serial-Auslesung mit 115200 Baud implementiert.
- MQTT-Discovery und Publishing für skalare Messwerte eingerichtet.
