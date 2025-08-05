#!/usr/bin/env python3
"""
GrowWiz Sensor Management
Handles reading from various sensors connected to Raspberry Pi
"""

import os
import time
import json
from typing import Dict, Any
from loguru import logger

try:
    import RPi.GPIO as GPIO
    import adafruit_dht
    import board
    from w1thermsensor import W1ThermSensor
    import smbus2
    RASPBERRY_PI = True
except ImportError:
    logger.warning("Raspberry Pi libraries not available. Running in simulation mode.")
    RASPBERRY_PI = False

class SensorManager:
    """Manages all sensor readings and hardware interfaces"""
    
    def __init__(self):
        self.config = self._load_config()
        self.simulation_mode = not RASPBERRY_PI
        
        if not self.simulation_mode:
            self._setup_gpio()
            self._setup_sensors()
        
        logger.info(f"SensorManager initialized (simulation_mode: {self.simulation_mode})")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load sensor configuration from environment"""
        return {
            "temperature_pin": int(os.getenv("TEMPERATURE_PIN", 4)),
            "humidity_pin": int(os.getenv("HUMIDITY_PIN", 4)),
            "soil_moisture_pin": int(os.getenv("SOIL_MOISTURE_PIN", 18)),
            "co2_sensor_address": int(os.getenv("CO2_SENSOR_ADDRESS", "0x61"), 16),
            "camera_enabled": os.getenv("CAMERA_ENABLED", "true").lower() == "true"
        }
    
    def _setup_gpio(self):
        """Initialize GPIO pins"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.config["soil_moisture_pin"], GPIO.IN)
            logger.info("GPIO pins configured successfully")
        except Exception as e:
            logger.error(f"Failed to setup GPIO: {e}")
            self.simulation_mode = True
    
    def _setup_sensors(self):
        """Initialize sensor objects"""
        try:
            # DHT22 for temperature and humidity
            self.dht_sensor = adafruit_dht.DHT22(getattr(board, f"D{self.config['temperature_pin']}"))
            
            # I2C bus for CO2 sensor
            self.i2c_bus = smbus2.SMBus(1)
            
            logger.info("Sensors initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize sensors: {e}")
            self.simulation_mode = True
    
    def read_temperature_humidity(self) -> Dict[str, float]:
        """Read temperature and humidity from DHT22 sensor"""
        if self.simulation_mode:
            return self._simulate_temp_humidity()
        
        try:
            temperature = self.dht_sensor.temperature
            humidity = self.dht_sensor.humidity
            
            if temperature is not None and humidity is not None:
                return {
                    "temperature": round(temperature, 1),
                    "humidity": round(humidity, 1)
                }
            else:
                logger.warning("Failed to read DHT22 sensor")
                return self._simulate_temp_humidity()
                
        except Exception as e:
            logger.error(f"Error reading DHT22: {e}")
            return self._simulate_temp_humidity()
    
    def read_soil_moisture(self) -> float:
        """Read soil moisture level"""
        if self.simulation_mode:
            return self._simulate_soil_moisture()
        
        try:
            # Read analog value from soil moisture sensor
            # This is a simplified implementation - actual implementation
            # would depend on your specific sensor and ADC setup
            raw_value = GPIO.input(self.config["soil_moisture_pin"])
            
            # Convert to percentage (0-100%)
            moisture_percent = (raw_value / 1024.0) * 100
            return round(moisture_percent, 1)
            
        except Exception as e:
            logger.error(f"Error reading soil moisture: {e}")
            return self._simulate_soil_moisture()
    
    def read_co2(self) -> float:
        """Read CO2 level from MH-Z19B sensor"""
        if self.simulation_mode:
            return self._simulate_co2()
        
        try:
            # Send command to CO2 sensor via I2C
            # This is a simplified implementation for MH-Z19B
            self.i2c_bus.write_byte(self.config["co2_sensor_address"], 0x86)
            time.sleep(0.1)
            
            # Read response
            data = self.i2c_bus.read_i2c_block_data(self.config["co2_sensor_address"], 0, 9)
            
            if len(data) >= 4:
                co2_value = (data[2] << 8) | data[3]
                return float(co2_value)
            else:
                logger.warning("Invalid CO2 sensor response")
                return self._simulate_co2()
                
        except Exception as e:
            logger.error(f"Error reading CO2 sensor: {e}")
            return self._simulate_co2()
    
    def read_all_sensors(self) -> Dict[str, Any]:
        """Read all sensor values and return as dictionary"""
        try:
            # Get temperature and humidity
            temp_humid = self.read_temperature_humidity()
            
            # Get other sensor readings
            soil_moisture = self.read_soil_moisture()
            co2_level = self.read_co2()
            
            sensor_data = {
                "temperature": temp_humid.get("temperature", 0.0),
                "humidity": temp_humid.get("humidity", 0.0),
                "soil_moisture": soil_moisture,
                "co2": co2_level,
                "timestamp": time.time(),
                "simulation_mode": self.simulation_mode
            }
            
            logger.debug(f"Sensor readings: {sensor_data}")
            return sensor_data
            
        except Exception as e:
            logger.error(f"Error reading sensors: {e}")
            return self._get_default_readings()
    
    def _simulate_temp_humidity(self) -> Dict[str, float]:
        """Simulate temperature and humidity readings for testing"""
        import random
        return {
            "temperature": round(random.uniform(20.0, 28.0), 1),
            "humidity": round(random.uniform(40.0, 65.0), 1)
        }
    
    def _simulate_soil_moisture(self) -> float:
        """Simulate soil moisture reading for testing"""
        import random
        return round(random.uniform(30.0, 80.0), 1)
    
    def _simulate_co2(self) -> float:
        """Simulate CO2 reading for testing"""
        import random
        return round(random.uniform(400.0, 1200.0), 1)
    
    def _get_default_readings(self) -> Dict[str, Any]:
        """Return default sensor readings in case of errors"""
        return {
            "temperature": 24.5,
            "humidity": 45.2,
            "soil_moisture": 72.0,
            "co2": 550.0,
            "timestamp": time.time(),
            "simulation_mode": True,
            "error": True
        }
    
    def get_sensor_status(self) -> Dict[str, Any]:
        """Get status information about all sensors"""
        return {
            "simulation_mode": self.simulation_mode,
            "raspberry_pi_available": RASPBERRY_PI,
            "config": self.config,
            "last_reading": self.read_all_sensors()
        }
    
    def cleanup(self):
        """Clean up GPIO resources"""
        if not self.simulation_mode:
            try:
                GPIO.cleanup()
                logger.info("GPIO cleanup completed")
            except Exception as e:
                logger.error(f"Error during GPIO cleanup: {e}")

# Example usage and testing
def read_sensors():
    """Legacy function for compatibility with your notes"""
    sensor_manager = SensorManager()
    return sensor_manager.read_all_sensors()

if __name__ == "__main__":
    # Test the sensor manager
    manager = SensorManager()
    
    try:
        for i in range(5):
            readings = manager.read_all_sensors()
            print(f"Reading {i+1}: {json.dumps(readings, indent=2)}")
            time.sleep(2)
    finally:
        manager.cleanup()