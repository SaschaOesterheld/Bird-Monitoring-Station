import bme680

class WeatherSensor:
    def __init__(self):
        self.sensor = None
        self.available = False
        self._init_sensor()

    def _init_sensor(self):
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
        self.sensor.altitude = 500
        self.sensor.set_humidity_oversample(bme680.OS_2X)
        self.sensor.set_pressure_oversample(bme680.OS_4X)
        self.sensor.set_temperature_oversample(bme680.OS_8X)
        self.sensor.set_filter(bme680.FILTER_SIZE_3)

    def read(self):
        """Always safe to call"""
        sensor_data=None
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
            print("Error in WeatherSemsor.py 43:")
            print(e)
            return None
