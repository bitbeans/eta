import logging
import sys
import traceback
import requests
import voluptuous as vol
import xml.etree.ElementTree as ET
from datetime import timedelta
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity, SensorStateClass, SensorDeviceClass
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
import homeassistant.helpers.config_validation as cv
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)
_LOGGER.debug("[ETA] Integration module initialized")
_LOGGER.debug("[ETA] Python version: %s, Home Assistant module path: %s", sys.version, sys.path)

CONF_POLLING = "polling"
CONF_SENSORS = "sensors"

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)

_LOGGER.debug("[ETA] Defining SENSOR_SCHEMA")
SENSOR_SCHEMA = vol.Schema({
    vol.Required('uri'): cv.string,
    vol.Required('name'): cv.string,
    vol.Optional('unit'): vol.Any(cv.string, None),
    vol.Optional('factor'): cv.positive_float,
    vol.Optional('decimals'): cv.positive_int,
    vol.Optional('device_class'): vol.Any(cv.string, None),
    vol.Optional('state_class'): vol.Any(cv.string, None),
})

_LOGGER.debug("[ETA] Defining PLATFORM_SCHEMA")
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_USERNAME): cv.string,
    vol.Optional(CONF_PASSWORD): cv.string,
    vol.Required(CONF_NAME): cv.string,
    vol.Optional(CONF_PORT, default=8080): cv.port,
    vol.Optional(CONF_POLLING, default=30): cv.positive_int,
    vol.Optional(CONF_SENSORS, default=[]): vol.All(cv.ensure_list, [SENSOR_SCHEMA]),
})

def setup_platform(hass, config, add_entities, discovery_info=None):
    _LOGGER.debug("[ETA] Starting setup of ETA platform")
    try:
        _LOGGER.debug("[ETA] Received configuration: %s", config)
        _LOGGER.debug("[ETA] Validating platform configuration")
        try:
            validated_config = PLATFORM_SCHEMA(config)
            _LOGGER.debug("[ETA] Platform configuration validated successfully: %s", validated_config)
        except vol.Invalid as e:
            _LOGGER.error("[ETA] Configuration validation failed: %s", str(e))
            raise

        host = validated_config[CONF_HOST]
        port = validated_config[CONF_PORT]
        username = validated_config.get(CONF_USERNAME)
        password = validated_config.get(CONF_PASSWORD)
        name = validated_config[CONF_NAME]
        polling = validated_config[CONF_POLLING]

        _LOGGER.debug("[ETA] Configuring ETAHeater with host=%s, port=%s, name=%s", host, port, name)
        eta = ETAHeater(host, port, username, password, name)

        sensors_config = validated_config.get(CONF_SENSORS)
        if not sensors_config:
            _LOGGER.debug("[ETA] No sensors specified in config, loading default sensors")
            try:
                from .sensors_default import SENSORS_DEFAULT
                sensors_config = SENSORS_DEFAULT
                _LOGGER.debug("[ETA] Loaded default sensors: %s", sensors_config)
            except ImportError as e:
                _LOGGER.error("[ETA] Failed to import sensors_default: %s", str(e))
                raise

        sensors = []
        for sensor_config in sensors_config:
            try:
                _LOGGER.debug("[ETA] Validating sensor config: %s", sensor_config)
                validated_sensor_config = SENSOR_SCHEMA(sensor_config)
                sensor = ETASensor(eta, validated_sensor_config)
                sensors.append(sensor)
                _LOGGER.debug("[ETA] Added sensor: %s", sensor._attr_name)
            except vol.Invalid as e:
                _LOGGER.error("[ETA] Invalid sensor configuration: %s", str(e))
                continue

        if not sensors:
            _LOGGER.error("[ETA] No valid sensors configured, platform setup failed")
            return

        _LOGGER.debug("[ETA] Adding %d sensors to Home Assistant", len(sensors))
        add_entities(sensors, True)
        _LOGGER.debug("[ETA] Sensors added successfully")

        def set_value_service(call):
            uri = call.data.get('uri')
            value = call.data.get('value')
            try:
                eta.set_eta_value(uri, value)
                _LOGGER.info("[ETA] Successfully set value for %s to %s", uri, value)
            except Exception as e:
                _LOGGER.error("[ETA] Failed to set value for %s: %s", uri, str(e))

        _LOGGER.debug("[ETA] Registering eta.set_value service")
        try:
            hass.services.register('eta', 'set_value', set_value_service, schema=vol.Schema({
                vol.Required('uri'): cv.string,
                vol.Required('value'): cv.string,
            }))
            _LOGGER.debug("[ETA] Successfully registered eta.set_value service")
        except Exception as e:
            _LOGGER.error("[ETA] Failed to register eta.set_value service: %s", str(e))
            raise

        _LOGGER.debug("[ETA] ETA platform setup completed successfully")
    except Exception as e:
        _LOGGER.error("[ETA] Failed to set up ETA platform: %s", str(e))
        _LOGGER.error("[ETA] Exception traceback: %s", traceback.format_exc())
        raise

class ETAHeater:
    def __init__(self, host, port, username, password, name):
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._name = name
        self._base_url = f"http://{host}:{port}"

    def get_data(self, uri):
        try:
            auth = (self._username, self._password) if self._username and self._password else None
            _LOGGER.debug("[ETA] Fetching data from URL: %s", f"{self._base_url}{uri}")
            response = requests.get(
                f"{self._base_url}{uri}",
                auth=auth,
                timeout=10
            )
            response.raise_for_status()
            _LOGGER.debug("[ETA] Received response: %s", response.text)
            xml_data = ET.fromstring(response.text)
            _LOGGER.debug("[ETA] Parsed XML: %s", ET.tostring(xml_data, encoding='unicode'))
            return xml_data
        except requests.exceptions.RequestException as e:
            _LOGGER.error("[ETA] Error fetching data from %s: %s", uri, str(e))
            return None
        except ET.ParseError as e:
            _LOGGER.error("[ETA] Failed to parse XML from %s: %s", uri, str(e))
            return None

    def set_eta_value(self, uri, value):
        try:
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            auth = (self._username, self._password) if self._username and self._password else None
            _LOGGER.debug("[ETA] Setting value for %s to %s", uri, value)
            response = requests.post(
                f"{self._base_url}{uri}",
                auth=auth,
                data={"value": value},
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            _LOGGER.debug("[ETA] Successfully set %s to %s", uri, value)
        except requests.exceptions.RequestException as e:
            _LOGGER.error("[ETA] Failed to set %s to %s: %s", uri, value, str(e))
            raise

class ETASensor(SensorEntity):
    def __init__(self, eta, config):
        super().__init__()
        self._eta = eta
        self._uri = config['uri']
        self._attr_name = f"ETA {config['name']}"
        self._attr_unique_id = f"eta_sensor_{config['uri'].replace('/', '_')}"
        self._attr_unit_of_measurement = config.get('unit')  # Verwende Einheit direkt
        self._attr_device_class = config.get('device_class')
        self._attr_state_class = config.get('state_class')
        self._factor = config.get('factor', 1.0)
        self._decimals = config.get('decimals', 0)
        self._state = None
        self._attributes = {}

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        _LOGGER.debug("[ETA] Updating sensor: %s", self._attr_name)
        data = self._eta.get_data(self._uri)
        if data is None:
            _LOGGER.warning("[ETA] No data received for sensor %s", self._attr_name)
            self._state = None
            return

        namespaces = {'eta': 'http://www.eta.co.at/rest/v1'}
        value = data.find(".//eta:value", namespaces)
        if value is None:
            _LOGGER.error("[ETA] No <value> element found in XML for sensor %s", self._attr_name)
            self._state = None
            return

        # Für Textstatus-Sensoren (z. B. Puffer Status) direkt strValue verwenden
        if self._attr_device_class == 'status':
            self._state = value.attrib.get('strValue', 'unknown')
            self._attributes = {k: v for k, v in value.attrib.items() if k not in ['uri', 'unit']}
            _LOGGER.debug("[ETA] Updated sensor %s with strValue: %s", self._attr_name, self._state)
        else:
            # Für numerische Sensoren
            try:
                # Sonderfall für Gesamt Energieverbrauch: Multiplikation mit Faktor
                if self._uri == "/user/var/40/10021/0/0/12016":
                    raw_value = float(value.text) * self._factor  # Multiplikation für kWh
                else:
                    raw_value = float(value.text) / self._factor  # Division für andere Sensoren
                self._state = round(raw_value, self._decimals) if self._decimals > 0 else int(raw_value)
                self._attributes = {k: v for k, v in value.attrib.items() if k not in ['uri', 'unit']}
                _LOGGER.debug("[ETA] Updated sensor %s with value: %s, unit: %s", self._attr_name, self._state, self._attr_unit_of_measurement)
            except (ValueError, TypeError) as e:
                _LOGGER.error("[ETA] Failed to process value for sensor %s: %s", self._attr_name, str(e))
                self._state = value.attrib.get('strValue', 'unknown')
                self._attributes = {k: v for k, v in value.attrib.items() if k not in ['uri', 'unit']}

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attributes