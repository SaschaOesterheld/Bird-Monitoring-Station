"""
Interface for the BME680 environmental sensor.

This module provides a lightweight wrapper around the BME680 sensor for
reading ambient temperature, humidity, and atmospheric pressure via I²C.
The wrapper automatically detects the sensor address, applies a default
configuration, and safely handles missing or unavailable hardware.
"""

import bme680


class WeatherSensor:
    """
    Wrapper around a BME680 environmental sensor.

    The class automatically initializes and configures the sensor and
    provides a fault-tolerant interface for retrieving weather data.
    """

    def __init__(self, height_above_sea_level=500):
        """
        Initialize the weather sensor.

        Args:
            height_above_sea_level: Installation altitude in metres above
                sea level. Used by the sensor for pressure compensation.
        """
        self.sensor = None
        self.available = False
        self.height = height_above_sea_level
        self._init_sensor()

    def _init_sensor(self):
        """
        Detect and configure the BME680 sensor.

        The primary and secondary I²C addresses are probed until a sensor
        is found. If successful, default oversampling and filtering
        settings are applied.
        """
        for addr in (bme680.I2C_ADDR_PRIMARY, bme680.I2C_ADDR_SECONDARY):
            try:
                self.sensor = bme680.BME680(addr)
                self.available = True
                break
            except (RuntimeError, IOError):
                pass

        if not self.available:
            return

        # Safe configuration
        self.sensor.altitude = self.height
        self.sensor.set_humidity_oversample(bme680.OS_2X)
        self.sensor.set_pressure_oversample(bme680.OS_4X)
        self.sensor.set_temperature_oversample(bme680.OS_8X)
        self.sensor.set_filter(bme680.FILTER_SIZE_3)

    def read(self):
        """
        Read the latest weather measurements.

        Returns:
            A dictionary containing temperature (°C), pressure (hPa),
            and relative humidity (%), or ``None`` if the sensor is
            unavailable or no new measurement is available.
        """
        sensor_data = None

        if not self.available:
            print("Weather Sensor not available!")
            return None

        try:
            new_sensor_data_is_present = self.sensor.get_sensor_data()

            if not new_sensor_data_is_present:
                return None

            sensor_data = self.sensor.data

            return {
                "temperature": round(sensor_data.temperature, 2),
                "pressure": round(sensor_data.pressure, 2),
                "humidity": round(sensor_data.humidity, 2),
            }

        except (RuntimeError, IOError) as e:
            print("Error while reading weather sensor:")
            print(e)
            return None
