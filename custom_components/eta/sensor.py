import logging
import requests
import voluptuous as vol
import xml.etree.ElementTree as ET
from datetime import timedelta
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
import homeassistant.helpers.config_validation as cv
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

CONF_POLLING = "polling"
CONF_SENSORS = "sensors"

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)

SENSOR_SCHEMA = vol.Schema({
    vol.Required('uri'): cv.string,
    vol.Required('name'): cv.string,
    vol.Optional('unit'): cv.string,
    vol.Optional('scale'): cv.positive_int,
    vol.Optional('decimals'): cv.positive_int,
})

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
    host = config[CONF_HOST]
    port = config[CONF_PORT]
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    name = config[CONF_NAME]
    polling = config[CONF_POLLING]

    eta = ETAHeater(host, port, username, password, name)

    # Use default sensors from sensors_default.py if no sensors are specified
    sensors_config = config.get(CONF_SENSORS)
    if not sensors_config:
        from .sensors_default import SENSOR_DEFAULT
        sensors_config = SENSOR_DEFAULT
        _LOGGER.debug("No sensors specified in config, using default sensors from sensors_default.py")

    sensors = []
    for sensor_config in sensors_config:
        sensors.append(ETASensor(eta, sensor_config))

    add_entities(sensors, True)

    # Register service to set ETA values
    def set_value_service(call):
        uri = call.data.get('uri')
        value = call.data.get('value')
        try:
            eta.set_eta_value(uri, value)
            _LOGGER.info(f"Successfully set value for {uri} to {value}")
        except Exception as e:
            _LOGGER.error(f"Failed to set value for {uri}: {str(e)}")

    hass.services.register('eta', 'set_value', set_value_service, schema=vol.Schema({
        vol.Required('uri'): cv.string,
        vol.Required('value'): cv.string,
    }))

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
            response = requests.get(
                f"{self._base_url}{uri}",
                auth=auth,
                timeout=10
           
            response.raise_for_status()
            return ET.fromstring(response.content)
        except Exception as e:
            _LOGGER.error(f"Error fetching data from {uri}: {str(e)}")
            return None

    def set_eta_value(self, uri, value):
        """Set a value for the given URI via POST request."""
        try:
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            auth = (self._username, self._password) if self._username and self._password else None
            response = requests.post(
                f"{self._base_url}{uri}",
                auth=auth,
                data={"value": value},
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            _LOGGER.debug(f"Successfully set {uri} to {value}")
        except Exception as e:
            _LOGGER.error(f"Failed to set {uri} to {value}: {str(e)}")
            raise

class ETASensor:
    def __init__(self, eta, config):
        self._eta = eta
        self._uri = config['uri']
        self._name = config['name']
        self._unit = config.get('unit')
        self._scale = config.get('scale', 1)
        self._decimals = config.get('decimals', 0)
        self._state = None
        self._attributes = {}

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        data = self._eta.get_data(self._uri)
        if data is None:
            return

        value = data.find(".//value")
        if value is not None:
            try:
                raw_value = float(value.text) / self._scale
                self._state = round(raw_value, self._decimals) if self._decimals > 0 else int(raw_value)
                self._attributes = {k: v for k, v in value.attrib.items() if k != 'uri'}
            except (ValueError, TypeError):
                self._state = value.attrib.get('strValue', 'unknown')
                self._attributes = {k: v for k, v in value.attrib.items() if k != 'uri'}

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def unit_of_measurement(self):
        return self._unit

    @property
    def device_state_attributes(self):
        return self._attributes