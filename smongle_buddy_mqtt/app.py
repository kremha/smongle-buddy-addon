import json
import logging
import os
import time

import serial
import paho.mqtt.client as mqtt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)
_LOGGER = logging.getLogger("smongle_buddy")

with open("/data/options.json", "r", encoding="utf-8") as f:
    OPTIONS = json.load(f)

MQTT_HOST = OPTIONS["mqtt_host"]
MQTT_PORT = int(OPTIONS["mqtt_port"])
MQTT_USERNAME = OPTIONS["mqtt_username"]
MQTT_PASSWORD = OPTIONS["mqtt_password"]
SERIAL_DEVICE = OPTIONS["serial_device"]
# WICHTIG: Hier mussen OPERATION_MODE und POLL_INTERVAL definiert werden
OPERATION_MODE = OPTIONS.get("operation_mode", "Automatik (PUSH)")
POLL_INTERVAL = int(OPTIONS.get("poll_interval", 5)) * 60  # Minuten in Sekunden umrechnen

BASE_TOPIC = "smongle_buddy"
DISCOVERY_PREFIX = "homeassistant"
DEVICE = {
    "identifiers": ["smongle_buddy_usb"],
    "name": "Smongle Buddy",
    "manufacturer": "mechsat e.U.",
    "model": "Smongle Buddy",
}

# Nur skalare Messwerte werden als eigene HA-Entitäten angelegt.
SENSORS = {
    "home_live_w": ("Haus Leistung aktuell", "W", "power", "measurement"),
    "home_l1_voltage_v": ("Haus Spannung L1", "V", "voltage", "measurement"),
    "home_l2_voltage_v": ("Haus Spannung L2", "V", "voltage", "measurement"),
    "home_l3_voltage_v": ("Haus Spannung L3", "V", "voltage", "measurement"),
    "home_l1_current_a": ("Haus Strom L1", "A", "current", "measurement"),
    "home_l2_current_a": ("Haus Strom L2", "A", "current", "measurement"),
    "home_l3_current_a": ("Haus Strom L3", "A", "current", "measurement"),
    "home_counter_export_wh": ("Haus Zaehler Einspeisung", "Wh", "energy", "total_increasing"),
    "home_counter_import_wh": ("Haus Zaehler Bezug", "Wh", "energy", "total_increasing"),
    "home_today_energy_export_wh": ("Haus Energie Einspeisung heute", "Wh", "energy", "measurement"),
    "home_today_energy_import_wh": ("Haus Energie Bezug heute", "Wh", "energy", "measurement"),
    "buddy_rssi_dbm": ("Buddy WLAN Signal", "dBm", "signal_strength", "measurement"),
    "smongle_rssi_dbm": ("Smongle WLAN Signal", "dBm", "signal_strength", "measurement"),
    "eg_live_w": ("Energiegemeinschaft Leistung aktuell", "W", "power", "measurement"),
    "eg_today_export_percent": ("EG Einspeisung heute", "%", None, "measurement"),
    "eg_today_import_percent": ("EG Bezug heute", "%", None, "measurement"),
    "eg_today_energy_export_wh": ("EG Energie Einspeisung heute", "Wh", "energy", "measurement"),
    "eg_today_energy_import_wh": ("EG Energie Bezug heute", "Wh", "energy", "measurement"),
    "eg_name": ("Energiegemeinschaft Name", None, None, None),
}

mqtt_client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id="smongle_buddy_bridge",
)
mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        _LOGGER.info("Mit MQTT-Broker %s:%s verbunden", MQTT_HOST, MQTT_PORT)
        publish_discovery(client)
    else:
        _LOGGER.error("MQTT-Verbindung fehlgeschlagen: %s", reason_code)


mqtt_client.on_connect = on_connect


def publish_discovery(client):
    for key, (friendly_name, unit, device_class, state_class) in SENSORS.items():
        config = {
            "name": friendly_name,
            "unique_id": f"smongle_buddy_{key}",
            "state_topic": f"{BASE_TOPIC}/data",
            "value_template": "{{ value_json." + key + " }}",
            "unit_of_measurement": unit,
            "state_class": state_class,
            "device": DEVICE,
        }
        if device_class:
            config["device_class"] = device_class
        topic = f"{DISCOVERY_PREFIX}/sensor/smongle_buddy/{key}/config"
        client.publish(topic, json.dumps(config), qos=1, retain=True)
    _LOGGER.info("MQTT Discovery-Konfigurationen veröffentlicht")


def read_json_object(ser, timeout_seconds=10):
    """Liest zeilenweise ein und baut das mehrzeilige JSON-Objekt zusammen."""
    deadline = time.monotonic() + timeout_seconds
    buffer_lines = []

    while time.monotonic() < deadline:
        line = ser.readline()
        if not line:
            continue
        try:
            line_str = line.decode("utf-8", errors="ignore").strip()
            if not line_str:
                continue  # Leere Zeilen überspringen
            
            buffer_lines.append(line_str)
            combined = "".join(buffer_lines)
            
            # Prüfen, ob das JSON-Objekt komplett ist
            if combined.startswith("{") and combined.endswith("}"):
                return json.loads(combined)
        except json.JSONDecodeError:
            # Wenn das JSON noch unvollständig ist, wird einfach weitergelesen
            continue
        except Exception as exc:
            raise exc

    raise TimeoutError("Timeout: Kein vollständiges JSON-Objekt empfangen")


def main():
    _LOGGER.info("Smongle-Buddy MQTT-Bridge startet")
    _LOGGER.info("Modus: %s, Seriell: %s, 115200 Baud; MQTT: %s:%s", OPERATION_MODE, SERIAL_DEVICE, MQTT_HOST, MQTT_PORT)

    mqtt_client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    mqtt_client.loop_start()

    while True:
        try:
            with serial.Serial(
                SERIAL_DEVICE,
                baudrate=115200,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1.0,  # Kurzer Timeout für nicht-blockierendes Lesen im Push-Modus
                write_timeout=10,
            ) as ser:
                _LOGGER.info("Serielle Schnittstelle geöffnet")
                time.sleep(2)
                ser.reset_input_buffer()
                
                # Für den PULL-Modus Timer-Steuerung
                next_poll_time = 0.0

                while True:
                    current_time = time.monotonic()

                    # Nur im manuellen Modus nach Ablauf des Intervalls aktiv abfragen
                    if OPERATION_MODE == "Manuell (PULL)":
                        if current_time >= next_poll_time:
                            ser.write(b"api\n")
                            ser.flush()
                            next_poll_time = current_time + POLL_INTERVAL
                    
                    try:
                        # Im PUSH-Modus unendlich warten (bzw. bis Daten kommen), im PULL mit kurzem Timeout lesen
                        timeout_val = 60.0 if OPERATION_MODE == "Automatik (PUSH)" else 2.0
                        payload = read_json_object(ser, timeout_seconds=timeout_val)
                        
                        if payload and payload.get("status") == "ok":
                            encoded = json.dumps(payload, separators=(",", ":"))
                            info = mqtt_client.publish(f"{BASE_TOPIC}/data", encoded, qos=1, retain=True)
                            info.wait_for_publish(timeout=5)
                            _LOGGER.info("JSON-Daten veröffentlicht (%d Felder)", len(payload))
                    except TimeoutError:
                        # Im Push-Modus ist ein Timeout normal, wenn gerade keine Daten gesendet werden -> einfach weiterlauschen
                        if OPERATION_MODE == "Manuell (PULL)":
                            pass
                    except Exception as e:
                        _LOGGER.warning("Fehler beim Lesen/Parsen der Daten: %s", e)
                    
                    # Kleiner CPU-Schutz im Push-Modus
                    if OPERATION_MODE == "Automatik (PUSH)":
                        time.sleep(0.1)
                        
        except KeyboardInterrupt:
            break
        except Exception as exc:
            _LOGGER.exception("Fehler bei Serial/MQTT: %s; neuer Versuch in 10 Sekunden", exc)
            time.sleep(10)

    mqtt_client.loop_stop()
    mqtt_client.disconnect()


if __name__ == "__main__":
    main()
