"""
Sensor configuration for ETA integration.
- 'uri' is required: The API endpoint for the sensor (e.g., '/120/10601/0/0/12197').
- 'name' is required: The display name of the sensor in Home Assistant.
- 'unit' is optional: The unit of measurement (e.g., '°C', 'kW', '%'). Can be a string or Home Assistant unit enum.
- 'factor' is optional: Scaling factor for the sensor value (default: 1.0).
- 'decimals' is optional: Number of decimal places for the sensor value (default: 0).
- 'device_class' is optional: Home Assistant device class (e.g., 'temperature', 'energy').
- 'state_class' is optional: Home Assistant state class (e.g., 'measurement', 'total_increasing').
"""
from homeassistant.components.sensor import SensorStateClass, SensorDeviceClass
from homeassistant.const import UnitOfTemperature, UnitOfPower, UnitOfMass, UnitOfEnergy, PERCENTAGE

SENSORS_DEFAULT = [
    {
        "uri": "/user/var/120/10601/0/0/12208",
        "name": "Puffer Status",
        "unit": "",
        "factor": 1.0,
        "decimals": 0,
        "device_class": None,
        "state_class": None,
    },
    {
        "uri": "/user/var/120/10601/0/0/12197",
        "name": "Außentemperatur",
        "unit": UnitOfTemperature.CELSIUS,
        "factor": 10.0,
        "decimals": 1,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    {
        "uri": "/user/var/40/10021/0/0/12077",
        "name": "Angeforderte Leistung",
        "unit": UnitOfPower.KILO_WATT,
        "factor": 1.0,
        "decimals": 2,
        "device_class": SensorDeviceClass.POWER,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    {
        "uri": "/user/var/40/10021/0/0/12006",
        "name": "Angeforderte Temperatur",
        "unit": UnitOfTemperature.CELSIUS,
        "factor": 10.0,
        "decimals": 1,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    {
        "uri": "/user/var/40/10021/0/11109/0",
        "name": "Kessel",
        "unit": UnitOfTemperature.CELSIUS,
        "factor": 10.0,
        "decimals": 1,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    {
        "uri": "/user/var/40/10021/0/11110/0",
        "name": "Abgas",
        "unit": UnitOfTemperature.CELSIUS,
        "factor": 10.0,
        "decimals": 1,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    {
        "uri": "/user/var/40/10201/0/0/12015",
        "name": "Pelletsvorrat",
        "unit": UnitOfMass.KILOGRAMS,
        "factor": 10.0,
        "decimals": 0,
        "device_class": SensorDeviceClass.WEIGHT,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    {
        "uri": "/user/var/120/10601/0/0/12528",
        "name": "Puffer geladen",
        "unit": PERCENTAGE,
        "factor": 10.0,
        "decimals": 1,
        "device_class": SensorDeviceClass.BATTERY,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    {
        "uri": "/user/var/120/10601/0/0/13932",
        "name": "Warmwasser Aus Fühler",
        "unit": UnitOfTemperature.CELSIUS,
        "factor": 10.0,
        "decimals": 1,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    {
        "uri": "/user/var/40/10021/0/0/12016",
        "name": "Gesamt Energieverbrauch",
        "unit": UnitOfEnergy.KILO_WATT_HOUR,
        "device_class": SensorDeviceClass.ENERGY,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "factor": 0.48,  # 4.8 kWh/kg / scaleFactor 10
        "decimals": 1,
    },
]