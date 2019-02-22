"""
Support for displaying weather info from Gismeteo API.
"""
import logging
import voluptuous as vol

from datetime import datetime, timedelta, timezone
import urllib.request
import xml.etree.ElementTree as ET

from homeassistant.components.weather import (
    ATTR_FORECAST_CONDITION, ATTR_FORECAST_TEMP, ATTR_FORECAST_TEMP_LOW, ATTR_FORECAST_PRECIPITATION,
    ATTR_FORECAST_TIME, ATTR_FORECAST_WIND_SPEED, ATTR_FORECAST_WIND_BEARING, PLATFORM_SCHEMA, WeatherEntity)
from homeassistant.const import (
    TEMP_CELSIUS, CONF_NAME, CONF_MODE)
from homeassistant.helpers import config_validation as cv
from homeassistant.util import Throttle

class mylogger():
    def debug(self, format, *args):
        print(format % args)
    def warning(self, format, *args):
        print(format % args)

if __name__ == '__main__':
    _LOGGER = mylogger()
else:
    _LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'Gismeteo'
CONF_CITY = 'city'
FORECAST_MODE = ['hourly', 'daily']
URL = "https://services.gismeteo.ru/inform-service/inf_ios/forecast/?city={}&lang=en"
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=300)
MMHG2HPA = 1.333223684
DIRECTIONS = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_MODE, default='hourly'): vol.In(FORECAST_MODE),
    vol.Required(CONF_CITY): cv.string,
})

def dt_to_utc(dt, offset):
    local_tz = timezone(timedelta(minutes=offset))
    local_dt = datetime.fromisoformat(dt)
    local_dt_with_tz = local_dt.replace(tzinfo=local_tz)
    utc_dt = local_dt_with_tz.astimezone(timezone.utc)
    return utc_dt.isoformat()

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Gismeteo weather"""

    name = config.get(CONF_NAME)
    city = config.get(CONF_CITY)
    mode = config.get(CONF_MODE)

    gismeteo = GismeteoWeather(name, city, mode)

    add_entities([gismeteo], True)

class GismeteoWeather(WeatherEntity):
    """Representation of Gismeteo weather"""

    def __init__(self, name, city, mode):
        """Initialize the Gismeteo weather platform."""
#        _LOGGER.debug('gismeteo: _init_: %s %s %s', name, city, mode)
        self._name = name
        self._city = city
        self._mode = mode
        self._temperature = None
        self._pressure = None
        self._condition = None
        self._humidity = None
        self._visibility = None
        self._wind_speed = None
        self._wind_bearing = None
        self._forecast = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def condition(self):
        """Return the current condition."""
        return self._condition

    @property
    def temperature(self):
        """Return the temperature."""
        return self._temperature

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def pressure(self):
        """Return the pressure."""
        return self._pressure

    @property
    def humidity(self):
        """Return the humidity."""
        return self._humidity

    @property
    def visibility(self):
        """Return the visibility."""
        return self._visibility

    @property
    def wind_speed(self):
        """Return the wind speed. !!! m/s !!!"""
        return self._wind_speed

    @property
    def wind_bearing(self):
        """Return the wind direction."""
        return self._wind_bearing

    @property
    def attribution(self):
        """Return the attribution."""
        return "Data provided by gismeteo.ru"

    @property
    def forecast(self):
        """Return the forecast array."""
        return self._forecast

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Get the latest state of the sensor."""
#        _LOGGER.debug('gismeteo: update')

        url = URL.format(self._city)
        resp = urllib.request.urlopen(url)
        xml = ET.parse(resp)

        offset = int(xml.find('location').get('tzone'))
        fact = xml.find('location/fact/values')

        self._temperature = float(fact.get('tflt'))
        self._pressure = round(float(fact.get('p')) * MMHG2HPA, 1)
        self._humidity = int(fact.get('hum'))
        self._wind_speed = int(fact.get('ws'))
        wd = int(fact.get('wd'))
        if wd > 0: wd = wd - 1
        self._wind_bearing = DIRECTIONS[wd]
        self._condition = fact.get('descr')
        self._visibility = None

        self._forecast = []

        if self._mode == 'daily':
            for d in xml.findall('location/day[@descr]'):
                data_out = {}
                data_out[ATTR_FORECAST_TIME] = dt_to_utc(d.get('date'), offset)
                data_out[ATTR_FORECAST_CONDITION] = d.get('descr')
                data_out[ATTR_FORECAST_TEMP_LOW] = int(d.get('tmin'))
                data_out[ATTR_FORECAST_TEMP] = int(d.get('tmax'))
                data_out[ATTR_FORECAST_WIND_SPEED] = int(d.get('ws'))
                wd = int(d.get('wd'))
                if wd > 0: wd = wd - 1
                data_out[ATTR_FORECAST_WIND_BEARING] = DIRECTIONS[wd]
                pr = float(d.get('prflt', 0))
                if pr == 0: pr = int(d.get('pr'))
                data_out[ATTR_FORECAST_PRECIPITATION] = pr
                self._forecast.append(data_out)

        if self._mode == 'hourly':
            for f in xml.findall('location/day/forecast'):
                v = f.find('values')
                ET.dump(v)
                data_out = {}
                data_out[ATTR_FORECAST_TIME] = dt_to_utc(f.get('valid'), offset)
                data_out[ATTR_FORECAST_CONDITION] = v.get('descr')
#                data_out[ATTR_FORECAST_TEMP_LOW] = int(d.get('tmin'))
                data_out[ATTR_FORECAST_TEMP] = int(v.get('t'))
                data_out[ATTR_FORECAST_WIND_SPEED] = int(v.get('ws'))
                wd = int(v.get('wd'))
                if wd > 0: wd = wd - 1
                data_out[ATTR_FORECAST_WIND_BEARING] = DIRECTIONS[wd]
                pr = float(v.get('prflt', 0))
                if pr == 0: pr = int(v.get('pr'))
                data_out[ATTR_FORECAST_PRECIPITATION] = pr
                self._forecast.append(data_out)

if __name__ == '__main__':
#    print(dt_to_utc('2019-02-22T05:00:00', 300))
#    quit()
    gismeteo = GismeteoWeather('gismeteo', '4517', 'hourly')
    gismeteo.update()
#    print(gismeteo.wind_bearing)
    for i in gismeteo.forecast:
        print(i)
