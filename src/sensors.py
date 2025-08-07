#!/usr/bin/env python3
"""
Sensor Management for GrowWiz
Handles all sensor readings and hardware interactions
"""

import os
import time
import json
import random
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from .config import config

# Try to import Raspberry Pi libraries
try:
    import RPi.GPIO as GPIO
    import Adafruit_DHT
    from w1thermsensor import W1ThermSensor
    RASPBERRY_PI_AVAILABLE = True
except ImportError:
    RASPBERRY_PI_AVAILABLE = False
    logging.warning("Raspberry Pi libraries not available. Running in simulation mode.")

class SensorManager:
    """Manages all sensor operations for the grow system"""
    
    def __init__(self, simulation_mode: bool = None):
        self.logger = logging.getLogger(__name__)
        self.sensor_config = config.get_sensor_config()
        
        # Determine simulation mode
        if simulation_mode is None:
            self.simulation_mode = (not RASPBERRY_PI_AVAILABLE or 
                                  config.should_use_simulation() or
                                  self.sensor_config.get('use_mock_sensors', False))
        else:
            self.simulation_mode = simulation_mode
            
        # Load test data if in testing mode
        self.test_data = None
        if config.is_testing_mode():
            self._load_test_data()
            
        if self.simulation_mode:
            self.logger.info("Sensor manager initialized in simulation mode")
        else:
            self.logger.info("Sensor manager initialized with hardware sensors")
            self._setup_hardware()
    
    def _load_test_data(self):
        """Load test sensor data for testing mode"""
        test_file = self.sensor_config.get('mock_data_file', 'test_data/sensor_readings.json')
        try:
            if os.path.exists(test_file):
                with open(test_file, 'r') as f:
                    self.test_data = json.load(f)
                    self.logger.info(f"Loaded test data from {test_file}")
        except Exception as e:
            self.logger.warning(f"Could not load test data: {e}")
    
    def _setup_hardware(self):
        """Initialize hardware sensors"""
        if not self.simulation_mode and RASPBERRY_PI_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            # Initialize sensor pins and configurations
            self.temp_sensor = Adafruit_DHT.DHT22
            self.temp_pin = self.sensor_config['temperature_pin']
            self.humidity_pin = self.sensor_config['humidity_pin']
            self.soil_moisture_pin = self.sensor_config['soil_moisture_pin']
    
    def get_temperature(self) -> float:
        """Get current temperature reading"""
        if self.simulation_mode:
            return self._get_test_or_simulated_value('temperature', self._simulate_temperature)
        else:
            # Real sensor reading logic here
            try:
                humidity, temperature = Adafruit_DHT.read_retry(self.temp_sensor, self.temp_pin)
                return temperature if temperature is not None else 0.0
            except Exception as e:
                self.logger.error(f"Temperature sensor error: {e}")
                return self._simulate_temperature()
    
    def get_humidity(self) -> float:
        """Get current humidity reading"""
        if self.simulation_mode:
            return self._get_test_or_simulated_value('humidity', self._simulate_humidity)
        else:
            # Real sensor reading logic here
            try:
                humidity, temperature = Adafruit_DHT.read_retry(self.temp_sensor, self.humidity_pin)
                return humidity if humidity is not None else 0.0
            except Exception as e:
                self.logger.error(f"Humidity sensor error: {e}")
                return self._simulate_humidity()
    
    def get_soil_moisture(self) -> float:
        """Get current soil moisture reading"""
        if self.simulation_mode:
            return self._get_test_or_simulated_value('soil_moisture', self._simulate_soil_moisture)
        else:
            # Real sensor reading logic here
            try:
                # This would involve ADC reading for analog soil moisture sensor
                return 0.0
            except Exception as e:
                self.logger.error(f"Soil moisture sensor error: {e}")
                return self._simulate_soil_moisture()
    
    def get_co2_level(self) -> int:
        """Get current CO2 level"""
        if self.simulation_mode:
            return self._get_test_or_simulated_value('co2', self._simulate_co2)
        else:
            # Real CO2 sensor reading logic here
            try:
                return 400
            except Exception as e:
                self.logger.error(f"CO2 sensor error: {e}")
                return self._simulate_co2()
    
    def get_all_readings(self) -> Dict[str, Any]:
        """Get all sensor readings at once"""
        return {
            'temperature': self.get_temperature(),
            'humidity': self.get_humidity(),
            'soil_moisture': self.get_soil_moisture(),
            'co2': self.get_co2_level(),
            'timestamp': datetime.now().isoformat(),
            'simulation_mode': self.simulation_mode,
            'testing_mode': config.is_testing_mode(),
            'environment': config.environment.value
        }
    
    def _get_test_or_simulated_value(self, sensor_type: str, simulation_func):
        """Get test data value or fall back to simulation"""
        if self.test_data and config.is_testing_mode():
            scenario = self.test_data.get('current_scenario', 'normal_conditions')
            scenarios = self.test_data.get('test_scenarios', {})
            if scenario in scenarios and sensor_type in scenarios[scenario]:
                return scenarios[scenario][sensor_type]
        
        return simulation_func()
    
    def set_test_scenario(self, scenario_name: str):
        """Set the current test scenario"""
        if self.test_data and scenario_name in self.test_data.get('test_scenarios', {}):
            self.test_data['current_scenario'] = scenario_name
            self.logger.info(f"Test scenario set to: {scenario_name}")
            return True
        return False
    
    def get_available_test_scenarios(self) -> list:
        """Get list of available test scenarios"""
        if self.test_data:
            return list(self.test_data.get('test_scenarios', {}).keys())
        return []
    
    def _simulate_temperature(self) -> float:
        """Simulate temperature reading (20-30°C range)"""
        base_temp = 24.0
        variation = random.uniform(-4.0, 6.0)
        return round(base_temp + variation, 1)
    
    def _simulate_humidity(self) -> float:
        """Simulate humidity reading (40-80% range)"""
        base_humidity = 60.0
        variation = random.uniform(-20.0, 20.0)
        return round(max(0, min(100, base_humidity + variation)), 1)
    
    def _simulate_soil_moisture(self) -> float:
        """Simulate soil moisture reading (20-80% range)"""
        base_moisture = 50.0
        variation = random.uniform(-30.0, 30.0)
        return round(max(0, min(100, base_moisture + variation)), 1)
    
    def _simulate_co2(self) -> int:
        """Simulate CO2 reading (300-1200 ppm range)"""
        base_co2 = 400
        variation = random.randint(-100, 800)
        return max(300, base_co2 + variation)
    
    def cleanup(self):
        """Clean up GPIO resources"""
        if not self.simulation_mode and RASPBERRY_PI_AVAILABLE:
            GPIO.cleanup()

# Example usage and testing
def read_sensors():
    """Legacy function for compatibility with your notes"""
    sensor_manager = SensorManager()
    return sensor_manager.get_all_readings()

if __name__ == "__main__":
    # Test the sensor manager
    manager = SensorManager()
    
    try:
        for i in range(5):
            readings = manager.get_all_readings()
            print(f"Reading {i+1}: {json.dumps(readings, indent=2)}")
            time.sleep(2)
    finally:
        manager.cleanup()