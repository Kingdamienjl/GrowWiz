"""
Unit tests for GrowWiz sensor module
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sensors import SensorManager

class TestSensorManager:
    """Test cases for SensorManager class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.sensor_manager = SensorManager()
    
    def teardown_method(self):
        """Clean up after tests"""
        if hasattr(self.sensor_manager, 'cleanup'):
            self.sensor_manager.cleanup()
    
    def test_initialization(self):
        """Test sensor manager initialization"""
        assert self.sensor_manager is not None
        assert hasattr(self.sensor_manager, 'config')
        assert hasattr(self.sensor_manager, 'simulation_mode')
    
    def test_simulation_mode_default(self):
        """Test that simulation mode is enabled by default"""
        assert self.sensor_manager.simulation_mode is True
    
    def test_load_config(self):
        """Test configuration loading"""
        config = self.sensor_manager._load_config()
        
        assert isinstance(config, dict)
        assert 'dht22_pin' in config
        assert 'soil_moisture_pin' in config
        assert 'co2_i2c_address' in config
    
    def test_simulate_sensor_data(self):
        """Test sensor data simulation"""
        data = self.sensor_manager._simulate_sensor_data()
        
        assert isinstance(data, dict)
        assert 'temperature' in data
        assert 'humidity' in data
        assert 'soil_moisture' in data
        assert 'co2' in data
        assert 'timestamp' in data
        
        # Check data ranges
        assert 15 <= data['temperature'] <= 35
        assert 20 <= data['humidity'] <= 80
        assert 10 <= data['soil_moisture'] <= 90
        assert 300 <= data['co2'] <= 1500
        assert isinstance(data['timestamp'], float)
    
    def test_read_all_sensors_simulation(self):
        """Test reading all sensors in simulation mode"""
        data = self.sensor_manager.read_all_sensors()
        
        assert isinstance(data, dict)
        assert 'temperature' in data
        assert 'humidity' in data
        assert 'soil_moisture' in data
        assert 'co2' in data
        assert 'timestamp' in data
        assert data['simulation_mode'] is True
    
    def test_read_temperature_simulation(self):
        """Test temperature reading in simulation mode"""
        temp = self.sensor_manager.read_temperature()
        
        assert isinstance(temp, (int, float))
        assert 15 <= temp <= 35
    
    def test_read_humidity_simulation(self):
        """Test humidity reading in simulation mode"""
        humidity = self.sensor_manager.read_humidity()
        
        assert isinstance(humidity, (int, float))
        assert 20 <= humidity <= 80
    
    def test_read_soil_moisture_simulation(self):
        """Test soil moisture reading in simulation mode"""
        moisture = self.sensor_manager.read_soil_moisture()
        
        assert isinstance(moisture, (int, float))
        assert 10 <= moisture <= 90
    
    def test_read_co2_simulation(self):
        """Test CO2 reading in simulation mode"""
        co2 = self.sensor_manager.read_co2()
        
        assert isinstance(co2, (int, float))
        assert 300 <= co2 <= 1500
    
    @patch('sensors.GPIO')
    def test_setup_gpio_mock(self, mock_gpio):
        """Test GPIO setup with mocked GPIO"""
        # Create a new sensor manager with hardware mode
        sensor_manager = SensorManager()
        sensor_manager.simulation_mode = False
        
        # Mock GPIO methods
        mock_gpio.setmode = Mock()
        mock_gpio.setup = Mock()
        mock_gpio.BCM = 'BCM'
        mock_gpio.IN = 'IN'
        mock_gpio.OUT = 'OUT'
        
        # Test GPIO setup
        sensor_manager._setup_gpio()
        
        # Verify GPIO calls
        mock_gpio.setmode.assert_called_once()
        assert mock_gpio.setup.call_count >= 1
    
    @patch('sensors.Adafruit_DHT')
    def test_read_dht22_mock(self, mock_dht):
        """Test DHT22 reading with mocked library"""
        # Create sensor manager in hardware mode
        sensor_manager = SensorManager()
        sensor_manager.simulation_mode = False
        
        # Mock DHT22 reading
        mock_dht.read_retry.return_value = (65.0, 23.5)  # humidity, temperature
        mock_dht.DHT22 = 'DHT22'
        
        # Test reading
        temp, humidity = sensor_manager._read_dht22()
        
        assert temp == 23.5
        assert humidity == 65.0
        mock_dht.read_retry.assert_called_once()
    
    @patch('sensors.MCP3008')
    def test_read_soil_moisture_mock(self, mock_mcp):
        """Test soil moisture reading with mocked MCP3008"""
        # Create sensor manager in hardware mode
        sensor_manager = SensorManager()
        sensor_manager.simulation_mode = False
        
        # Mock MCP3008 reading
        mock_adc = Mock()
        mock_adc.read_adc.return_value = 512  # Mid-range value
        mock_mcp.return_value = mock_adc
        
        # Test reading
        moisture = sensor_manager._read_soil_moisture()
        
        assert isinstance(moisture, (int, float))
        assert 0 <= moisture <= 100
    
    def test_data_validation(self):
        """Test sensor data validation"""
        # Test valid data
        valid_data = {
            'temperature': 25.0,
            'humidity': 60.0,
            'soil_moisture': 45.0,
            'co2': 800,
            'timestamp': time.time()
        }
        
        validated = self.sensor_manager._validate_data(valid_data)
        assert validated == valid_data
        
        # Test invalid data
        invalid_data = {
            'temperature': -100,  # Too low
            'humidity': 150,      # Too high
            'soil_moisture': 'invalid',  # Wrong type
            'co2': None,
            'timestamp': time.time()
        }
        
        validated = self.sensor_manager._validate_data(invalid_data)
        assert validated['temperature'] is None
        assert validated['humidity'] is None
        assert validated['soil_moisture'] is None
        assert validated['co2'] is None
    
    def test_error_handling(self):
        """Test error handling in sensor readings"""
        # Test with invalid configuration
        sensor_manager = SensorManager()
        sensor_manager.config = {}  # Empty config
        
        # Should not raise exception
        data = sensor_manager.read_all_sensors()
        assert isinstance(data, dict)
    
    def test_cleanup(self):
        """Test cleanup method"""
        # Should not raise exception
        self.sensor_manager.cleanup()
    
    def test_multiple_readings_consistency(self):
        """Test that multiple readings are consistent"""
        readings = []
        for _ in range(5):
            data = self.sensor_manager.read_all_sensors()
            readings.append(data)
            time.sleep(0.1)
        
        # All readings should have the same structure
        for reading in readings:
            assert 'temperature' in reading
            assert 'humidity' in reading
            assert 'soil_moisture' in reading
            assert 'co2' in reading
            assert 'timestamp' in reading
        
        # Timestamps should be increasing
        timestamps = [r['timestamp'] for r in readings]
        assert timestamps == sorted(timestamps)
    
    def test_sensor_status_check(self):
        """Test sensor status checking"""
        if hasattr(self.sensor_manager, 'check_sensor_status'):
            status = self.sensor_manager.check_sensor_status()
            assert isinstance(status, dict)
    
    def test_configuration_override(self):
        """Test configuration override"""
        custom_config = {
            'dht22_pin': 18,
            'soil_moisture_pin': 1,
            'co2_i2c_address': '0x62'
        }
        
        sensor_manager = SensorManager(config=custom_config)
        assert sensor_manager.config['dht22_pin'] == 18
        assert sensor_manager.config['soil_moisture_pin'] == 1
        assert sensor_manager.config['co2_i2c_address'] == '0x62'

class TestSensorIntegration:
    """Integration tests for sensor functionality"""
    
    def test_sensor_data_format(self):
        """Test that sensor data follows expected format"""
        sensor_manager = SensorManager()
        data = sensor_manager.read_all_sensors()
        
        # Check required fields
        required_fields = ['temperature', 'humidity', 'soil_moisture', 'co2', 'timestamp']
        for field in required_fields:
            assert field in data
        
        # Check data types
        assert isinstance(data['timestamp'], (int, float))
        
        # Numeric fields should be numbers or None
        numeric_fields = ['temperature', 'humidity', 'soil_moisture', 'co2']
        for field in numeric_fields:
            value = data[field]
            assert value is None or isinstance(value, (int, float))
    
    def test_sensor_reading_performance(self):
        """Test sensor reading performance"""
        sensor_manager = SensorManager()
        
        start_time = time.time()
        for _ in range(10):
            sensor_manager.read_all_sensors()
        end_time = time.time()
        
        # Should complete 10 readings in reasonable time (< 5 seconds)
        assert (end_time - start_time) < 5.0
    
    def test_concurrent_readings(self):
        """Test concurrent sensor readings"""
        import threading
        
        sensor_manager = SensorManager()
        results = []
        errors = []
        
        def read_sensors():
            try:
                data = sensor_manager.read_all_sensors()
                results.append(data)
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=read_sensors)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5
        
        # All results should be valid
        for result in results:
            assert isinstance(result, dict)
            assert 'temperature' in result

if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])