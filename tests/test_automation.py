"""
Unit tests for GrowWiz automation engine module
"""

import pytest
import sys
import os
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from automation import AutomationEngine, check_and_trigger

class TestAutomationEngine:
    """Test cases for AutomationEngine class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.engine = AutomationEngine()
        
        # Sample sensor data for testing
        self.sample_sensor_data = {
            'temperature': 25.0,
            'humidity': 45.0,
            'soil_moisture': 60.0,
            'co2': 500.0,
            'timestamp': datetime.now().isoformat()
        }
        
        self.extreme_sensor_data = {
            'temperature': 35.0,  # High
            'humidity': 25.0,     # Low
            'soil_moisture': 20.0, # Low
            'co2': 800.0,         # High
            'timestamp': datetime.now().isoformat()
        }
    
    def teardown_method(self):
        """Clean up after tests"""
        if hasattr(self.engine, 'cleanup'):
            self.engine.cleanup()
    
    def test_initialization(self):
        """Test automation engine initialization"""
        assert self.engine is not None
        assert hasattr(self.engine, 'rules')
        assert hasattr(self.engine, 'device_states')
        assert hasattr(self.engine, 'simulation_mode')
        assert isinstance(self.engine.rules, list)
        assert isinstance(self.engine.device_states, dict)
    
    def test_load_config(self):
        """Test configuration loading"""
        config = self.engine._load_config()
        
        assert isinstance(config, dict)
        assert 'thresholds' in config
        assert 'relay_pins' in config
        assert 'safety_limits' in config
        
        # Check threshold structure
        thresholds = config['thresholds']
        assert 'temperature' in thresholds
        assert 'humidity' in thresholds
        assert 'soil_moisture' in thresholds
        assert 'co2' in thresholds
        
        # Check relay pins
        relay_pins = config['relay_pins']
        assert 'fan' in relay_pins
        assert 'heater' in relay_pins
        assert 'humidifier' in relay_pins
        assert 'pump' in relay_pins
    
    def test_setup_gpio_simulation(self):
        """Test GPIO setup in simulation mode"""
        # Should not raise any exceptions in simulation mode
        self.engine._setup_gpio()
        
        assert self.engine.simulation_mode is True
    
    @patch('automation.GPIO')
    def test_setup_gpio_hardware(self, mock_gpio):
        """Test GPIO setup in hardware mode"""
        # Mock GPIO module
        mock_gpio.BCM = 'BCM'
        mock_gpio.OUT = 'OUT'
        mock_gpio.LOW = 0
        
        # Create engine in hardware mode
        engine = AutomationEngine()
        engine.simulation_mode = False
        
        # Test GPIO setup
        engine._setup_gpio()
        
        # Verify GPIO calls
        mock_gpio.setmode.assert_called_once_with('BCM')
        assert mock_gpio.setup.call_count > 0
        assert mock_gpio.output.call_count > 0
    
    def test_setup_default_rules(self):
        """Test default automation rules setup"""
        self.engine._setup_default_rules()
        
        assert len(self.engine.rules) > 0
        
        # Check rule structure
        for rule in self.engine.rules:
            assert 'name' in rule
            assert 'condition' in rule
            assert 'action' in rule
            assert 'device' in rule
            assert 'state' in rule
            assert callable(rule['condition'])
    
    def test_add_rule(self):
        """Test adding custom automation rules"""
        initial_count = len(self.engine.rules)
        
        # Add custom rule
        def custom_condition(data):
            return data.get('temperature', 0) > 30
        
        self.engine.add_rule(
            name='Custom Temperature Rule',
            condition=custom_condition,
            action='activate',
            device='custom_fan',
            state=True
        )
        
        assert len(self.engine.rules) == initial_count + 1
        
        # Check the added rule
        new_rule = self.engine.rules[-1]
        assert new_rule['name'] == 'Custom Temperature Rule'
        assert new_rule['device'] == 'custom_fan'
        assert new_rule['state'] is True
    
    def test_remove_rule(self):
        """Test removing automation rules"""
        # Add a rule first
        def test_condition(data):
            return True
        
        self.engine.add_rule(
            name='Test Rule',
            condition=test_condition,
            action='activate',
            device='test_device',
            state=True
        )
        
        initial_count = len(self.engine.rules)
        
        # Remove the rule
        removed = self.engine.remove_rule('Test Rule')
        
        assert removed is True
        assert len(self.engine.rules) == initial_count - 1
        
        # Try to remove non-existent rule
        removed = self.engine.remove_rule('Non-existent Rule')
        assert removed is False
    
    def test_check_rules_normal_conditions(self):
        """Test rule checking with normal sensor conditions"""
        # Setup default rules
        self.engine._setup_default_rules()
        
        # Check with normal sensor data
        triggered_actions = self.engine.check_rules(self.sample_sensor_data)
        
        assert isinstance(triggered_actions, list)
        # With normal conditions, few or no actions should be triggered
    
    def test_check_rules_extreme_conditions(self):
        """Test rule checking with extreme sensor conditions"""
        # Setup default rules
        self.engine._setup_default_rules()
        
        # Check with extreme sensor data
        triggered_actions = self.engine.check_rules(self.extreme_sensor_data)
        
        assert isinstance(triggered_actions, list)
        assert len(triggered_actions) > 0  # Should trigger multiple actions
        
        # Check action structure
        for action in triggered_actions:
            assert 'rule_name' in action
            assert 'device' in action
            assert 'action' in action
            assert 'timestamp' in action
    
    def test_activate_device_simulation(self):
        """Test device activation in simulation mode"""
        # Should not raise exceptions
        result = self.engine.activate_device('fan', True)
        
        assert result is True
        assert self.engine.device_states.get('fan') is True
        
        # Deactivate
        result = self.engine.activate_device('fan', False)
        assert result is True
        assert self.engine.device_states.get('fan') is False
    
    @patch('automation.GPIO')
    def test_activate_device_hardware(self, mock_gpio):
        """Test device activation in hardware mode"""
        # Mock GPIO
        mock_gpio.HIGH = 1
        mock_gpio.LOW = 0
        
        # Create engine in hardware mode
        engine = AutomationEngine()
        engine.simulation_mode = False
        engine.config = {
            'relay_pins': {'fan': 18}
        }
        
        # Test activation
        result = engine.activate_device('fan', True)
        
        assert result is True
        mock_gpio.output.assert_called_with(18, 1)
    
    def test_get_device_state(self):
        """Test getting device states"""
        # Set some device states
        self.engine.device_states['fan'] = True
        self.engine.device_states['heater'] = False
        
        assert self.engine.get_device_state('fan') is True
        assert self.engine.get_device_state('heater') is False
        assert self.engine.get_device_state('nonexistent') is None
    
    def test_get_all_device_states(self):
        """Test getting all device states"""
        # Set some device states
        self.engine.device_states['fan'] = True
        self.engine.device_states['heater'] = False
        
        states = self.engine.get_all_device_states()
        
        assert isinstance(states, dict)
        assert states['fan'] is True
        assert states['heater'] is False
    
    def test_emergency_stop(self):
        """Test emergency stop functionality"""
        # Set some devices as active
        self.engine.device_states['fan'] = True
        self.engine.device_states['heater'] = True
        self.engine.device_states['pump'] = True
        
        # Trigger emergency stop
        result = self.engine.emergency_stop()
        
        assert result is True
        
        # All devices should be deactivated
        for device, state in self.engine.device_states.items():
            assert state is False
    
    def test_process_sensor_data(self):
        """Test complete sensor data processing"""
        # Setup default rules
        self.engine._setup_default_rules()
        
        # Process normal data
        result = self.engine.process_sensor_data(self.sample_sensor_data)
        
        assert isinstance(result, dict)
        assert 'triggered_actions' in result
        assert 'device_states' in result
        assert 'timestamp' in result
        
        # Process extreme data
        result = self.engine.process_sensor_data(self.extreme_sensor_data)
        
        assert len(result['triggered_actions']) > 0
    
    def test_rule_conditions(self):
        """Test individual rule conditions"""
        # Setup default rules
        self.engine._setup_default_rules()
        
        # Test temperature rules
        high_temp_data = {'temperature': 32.0}
        low_temp_data = {'temperature': 18.0}
        
        # Find temperature rules
        temp_rules = [r for r in self.engine.rules if 'temperature' in r['name'].lower()]
        
        assert len(temp_rules) > 0
        
        # Test high temperature condition
        high_temp_rule = next((r for r in temp_rules if 'high' in r['name'].lower()), None)
        if high_temp_rule:
            assert high_temp_rule['condition'](high_temp_data) is True
            assert high_temp_rule['condition'](low_temp_data) is False
    
    def test_safety_limits(self):
        """Test safety limit enforcement"""
        # Create extreme conditions that should trigger safety
        dangerous_data = {
            'temperature': 45.0,  # Dangerously high
            'humidity': 90.0,     # Dangerously high
            'co2': 2000.0,        # Dangerously high
            'timestamp': datetime.now().isoformat()
        }
        
        # Setup default rules (includes safety rules)
        self.engine._setup_default_rules()
        
        # Process dangerous data
        result = self.engine.process_sensor_data(dangerous_data)
        
        # Should trigger safety actions
        safety_actions = [a for a in result['triggered_actions'] 
                         if 'safety' in a.get('rule_name', '').lower()]
        
        assert len(safety_actions) > 0
    
    def test_rule_priority(self):
        """Test rule execution priority"""
        # Add rules with different priorities
        def high_priority_condition(data):
            return data.get('temperature', 0) > 40
        
        def low_priority_condition(data):
            return data.get('temperature', 0) > 35
        
        self.engine.add_rule(
            name='High Priority Rule',
            condition=high_priority_condition,
            action='emergency_stop',
            device='all',
            state=False
        )
        
        self.engine.add_rule(
            name='Low Priority Rule',
            condition=low_priority_condition,
            action='activate',
            device='fan',
            state=True
        )
        
        # Test with high temperature
        high_temp_data = {'temperature': 42.0}
        triggered_actions = self.engine.check_rules(high_temp_data)
        
        # Both rules should trigger, but we can verify they're both present
        rule_names = [action['rule_name'] for action in triggered_actions]
        assert 'High Priority Rule' in rule_names
        assert 'Low Priority Rule' in rule_names
    
    def test_device_state_persistence(self):
        """Test that device states persist between rule checks"""
        # Activate a device
        self.engine.activate_device('fan', True)
        
        # Check state
        assert self.engine.get_device_state('fan') is True
        
        # Process sensor data (shouldn't change state unless rules trigger)
        self.engine.process_sensor_data(self.sample_sensor_data)
        
        # State should persist
        assert self.engine.get_device_state('fan') is True
    
    def test_error_handling(self):
        """Test error handling in automation engine"""
        # Test with invalid sensor data
        invalid_data = {'invalid_key': 'invalid_value'}
        
        # Should not raise exceptions
        result = self.engine.process_sensor_data(invalid_data)
        assert isinstance(result, dict)
        
        # Test with None data
        result = self.engine.process_sensor_data(None)
        assert isinstance(result, dict)
    
    def test_legacy_function(self):
        """Test legacy check_and_trigger function"""
        # Should not raise exceptions
        check_and_trigger(self.sample_sensor_data)
        check_and_trigger(self.extreme_sensor_data)

class TestAutomationRules:
    """Test specific automation rule logic"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.engine = AutomationEngine()
        self.engine._setup_default_rules()
    
    def test_temperature_control_rules(self):
        """Test temperature control rules"""
        # High temperature - should activate cooling
        high_temp_data = {'temperature': 32.0}
        actions = self.engine.check_rules(high_temp_data)
        
        cooling_actions = [a for a in actions if a['device'] in ['fan', 'exhaust_fan']]
        assert len(cooling_actions) > 0
        
        # Low temperature - should activate heating
        low_temp_data = {'temperature': 18.0}
        actions = self.engine.check_rules(low_temp_data)
        
        heating_actions = [a for a in actions if a['device'] == 'heater']
        assert len(heating_actions) > 0
    
    def test_humidity_control_rules(self):
        """Test humidity control rules"""
        # Low humidity - should activate humidifier
        low_humidity_data = {'humidity': 30.0}
        actions = self.engine.check_rules(low_humidity_data)
        
        humidifier_actions = [a for a in actions if a['device'] == 'humidifier']
        assert len(humidifier_actions) > 0
        
        # High humidity - should activate dehumidifier/fan
        high_humidity_data = {'humidity': 80.0}
        actions = self.engine.check_rules(high_humidity_data)
        
        dehumidify_actions = [a for a in actions if a['device'] in ['dehumidifier', 'fan']]
        assert len(dehumidify_actions) > 0
    
    def test_soil_moisture_rules(self):
        """Test soil moisture control rules"""
        # Low soil moisture - should activate pump
        dry_soil_data = {'soil_moisture': 25.0}
        actions = self.engine.check_rules(dry_soil_data)
        
        pump_actions = [a for a in actions if a['device'] == 'pump']
        assert len(pump_actions) > 0
    
    def test_co2_control_rules(self):
        """Test CO2 control rules"""
        # Low CO2 - should activate CO2 system
        low_co2_data = {'co2': 300.0}
        actions = self.engine.check_rules(low_co2_data)
        
        co2_actions = [a for a in actions if a['device'] == 'co2_valve']
        assert len(co2_actions) > 0

class TestAutomationIntegration:
    """Integration tests for automation engine"""
    
    def test_complete_automation_cycle(self):
        """Test complete automation cycle"""
        engine = AutomationEngine()
        engine._setup_default_rules()
        
        # Simulate a day cycle with changing conditions
        conditions = [
            {'temperature': 20.0, 'humidity': 60.0, 'soil_moisture': 70.0, 'co2': 400.0},  # Morning
            {'temperature': 28.0, 'humidity': 45.0, 'soil_moisture': 60.0, 'co2': 350.0},  # Midday
            {'temperature': 32.0, 'humidity': 35.0, 'soil_moisture': 40.0, 'co2': 300.0},  # Hot afternoon
            {'temperature': 25.0, 'humidity': 55.0, 'soil_moisture': 50.0, 'co2': 450.0},  # Evening
        ]
        
        results = []
        for condition in conditions:
            condition['timestamp'] = datetime.now().isoformat()
            result = engine.process_sensor_data(condition)
            results.append(result)
        
        # Verify all results are valid
        for result in results:
            assert isinstance(result, dict)
            assert 'triggered_actions' in result
            assert 'device_states' in result
            assert 'timestamp' in result
        
        # Hot afternoon should trigger the most actions
        hot_result = results[2]
        assert len(hot_result['triggered_actions']) > 0
    
    def test_automation_with_manual_override(self):
        """Test automation with manual device control"""
        engine = AutomationEngine()
        engine._setup_default_rules()
        
        # Manually activate a device
        engine.activate_device('fan', True)
        
        # Process sensor data that would normally deactivate the fan
        normal_data = {
            'temperature': 22.0,
            'humidity': 50.0,
            'timestamp': datetime.now().isoformat()
        }
        
        result = engine.process_sensor_data(normal_data)
        
        # Manual state should be maintained unless overridden by rules
        # This depends on rule implementation - some may override manual control
        assert isinstance(result, dict)
    
    def test_emergency_scenarios(self):
        """Test emergency scenario handling"""
        engine = AutomationEngine()
        engine._setup_default_rules()
        
        # Simulate emergency conditions
        emergency_data = {
            'temperature': 45.0,  # Extreme heat
            'humidity': 95.0,     # Extreme humidity
            'co2': 3000.0,        # Dangerous CO2 levels
            'timestamp': datetime.now().isoformat()
        }
        
        result = engine.process_sensor_data(emergency_data)
        
        # Should trigger emergency actions
        assert len(result['triggered_actions']) > 0
        
        # Test emergency stop
        stop_result = engine.emergency_stop()
        assert stop_result is True
        
        # All devices should be off
        states = engine.get_all_device_states()
        for device, state in states.items():
            assert state is False

if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])