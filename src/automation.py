#!/usr/bin/env python3
"""
GrowWiz Automation Engine
Handles automated responses to sensor readings and environmental control
"""

import os
import time
import json
from typing import Dict, Any, List, Callable
from dataclasses import dataclass
from loguru import logger

try:
    import RPi.GPIO as GPIO
    RASPBERRY_PI = True
except ImportError:
    logger.warning("Raspberry Pi GPIO not available. Running in simulation mode.")
    RASPBERRY_PI = False

@dataclass
class TriggerRule:
    """Represents an automation trigger rule"""
    name: str
    condition: Callable[[Dict[str, Any]], bool]
    action: Callable[[], None]
    cooldown_seconds: int = 300  # 5 minutes default cooldown
    enabled: bool = True
    last_triggered: float = 0.0
    description: str = ""

class AutomationEngine:
    """Manages automated responses to environmental conditions"""
    
    def __init__(self):
        self.simulation_mode = not RASPBERRY_PI
        self.rules: List[TriggerRule] = []
        self.device_states = {}
        self.config = self._load_config()
        
        if not self.simulation_mode:
            self._setup_gpio()
        
        self._setup_default_rules()
        logger.info(f"AutomationEngine initialized (simulation_mode: {self.simulation_mode})")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load automation configuration from environment"""
        return {
            # Relay pins for devices
            "humidifier_pin": int(os.getenv("HUMIDIFIER_RELAY_PIN", 17)),
            "fan_pin": int(os.getenv("FAN_RELAY_PIN", 27)),
            "heater_pin": int(os.getenv("HEATER_RELAY_PIN", 22)),
            "water_pump_pin": int(os.getenv("WATER_PUMP_RELAY_PIN", 23)),
            
            # Thresholds
            "temp_min": float(os.getenv("TEMP_MIN", 18)),
            "temp_max": float(os.getenv("TEMP_MAX", 28)),
            "humidity_min": float(os.getenv("HUMIDITY_MIN", 40)),
            "humidity_max": float(os.getenv("HUMIDITY_MAX", 60)),
            "soil_moisture_min": float(os.getenv("SOIL_MOISTURE_MIN", 30)),
            "soil_moisture_max": float(os.getenv("SOIL_MOISTURE_MAX", 80)),
            "co2_min": float(os.getenv("CO2_MIN", 400)),
            "co2_max": float(os.getenv("CO2_MAX", 1200))
        }
    
    def _setup_gpio(self):
        """Initialize GPIO pins for relay control"""
        try:
            GPIO.setmode(GPIO.BCM)
            
            # Setup relay pins as outputs
            relay_pins = [
                self.config["humidifier_pin"],
                self.config["fan_pin"],
                self.config["heater_pin"],
                self.config["water_pump_pin"]
            ]
            
            for pin in relay_pins:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.HIGH)  # Relays are typically active LOW
                self.device_states[f"pin_{pin}"] = False
            
            logger.info("GPIO pins configured for automation")
            
        except Exception as e:
            logger.error(f"Failed to setup GPIO: {e}")
            self.simulation_mode = True
    
    def _setup_default_rules(self):
        """Setup default automation rules"""
        
        # Temperature control rules
        self.add_rule(TriggerRule(
            name="low_temperature_heating",
            condition=lambda data: data.get("temperature", 25) < self.config["temp_min"],
            action=lambda: self.activate_device("heater", True),
            cooldown_seconds=300,
            description=f"Turn on heater when temperature < {self.config['temp_min']}°C"
        ))
        
        self.add_rule(TriggerRule(
            name="high_temperature_cooling",
            condition=lambda data: data.get("temperature", 25) > self.config["temp_max"],
            action=lambda: self.activate_device("fan", True),
            cooldown_seconds=300,
            description=f"Turn on fan when temperature > {self.config['temp_max']}°C"
        ))
        
        # Humidity control rules
        self.add_rule(TriggerRule(
            name="low_humidity_humidifier",
            condition=lambda data: data.get("humidity", 50) < self.config["humidity_min"],
            action=lambda: self.activate_device("humidifier", True),
            cooldown_seconds=600,  # 10 minutes cooldown for humidifier
            description=f"Turn on humidifier when humidity < {self.config['humidity_min']}%"
        ))
        
        self.add_rule(TriggerRule(
            name="high_humidity_ventilation",
            condition=lambda data: data.get("humidity", 50) > self.config["humidity_max"],
            action=lambda: self.activate_device("fan", True),
            cooldown_seconds=300,
            description=f"Turn on fan when humidity > {self.config['humidity_max']}%"
        ))
        
        # Soil moisture rules
        self.add_rule(TriggerRule(
            name="low_soil_moisture_watering",
            condition=lambda data: data.get("soil_moisture", 50) < self.config["soil_moisture_min"],
            action=lambda: self.water_plants(),
            cooldown_seconds=3600,  # 1 hour cooldown for watering
            description=f"Water plants when soil moisture < {self.config['soil_moisture_min']}%"
        ))
        
        # Safety shutoff rules
        self.add_rule(TriggerRule(
            name="temperature_normal_heater_off",
            condition=lambda data: (
                data.get("temperature", 25) > self.config["temp_min"] + 2 and
                self.device_states.get("heater", False)
            ),
            action=lambda: self.activate_device("heater", False),
            cooldown_seconds=60,
            description="Turn off heater when temperature is back to normal"
        ))
        
        self.add_rule(TriggerRule(
            name="humidity_normal_humidifier_off",
            condition=lambda data: (
                data.get("humidity", 50) > self.config["humidity_min"] + 5 and
                self.device_states.get("humidifier", False)
            ),
            action=lambda: self.activate_device("humidifier", False),
            cooldown_seconds=60,
            description="Turn off humidifier when humidity is back to normal"
        ))
        
        logger.info(f"Setup {len(self.rules)} default automation rules")
    
    def add_rule(self, rule: TriggerRule):
        """Add a new automation rule"""
        self.rules.append(rule)
        logger.debug(f"Added automation rule: {rule.name}")
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove an automation rule by name"""
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                del self.rules[i]
                logger.info(f"Removed automation rule: {rule_name}")
                return True
        return False
    
    def check_and_trigger(self, sensor_data: Dict[str, Any]):
        """Check all rules and trigger actions if conditions are met"""
        current_time = time.time()
        triggered_rules = []
        
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            # Check cooldown period
            if current_time - rule.last_triggered < rule.cooldown_seconds:
                continue
            
            try:
                # Check if condition is met
                if rule.condition(sensor_data):
                    logger.info(f"Triggering rule: {rule.name}")
                    
                    # Execute action
                    rule.action()
                    
                    # Update last triggered time
                    rule.last_triggered = current_time
                    triggered_rules.append(rule.name)
                    
            except Exception as e:
                logger.error(f"Error executing rule {rule.name}: {e}")
        
        if triggered_rules:
            logger.info(f"Triggered {len(triggered_rules)} automation rules: {triggered_rules}")
        
        return triggered_rules
    
    def activate_device(self, device_name: str, state: bool):
        """Activate or deactivate a device"""
        try:
            pin_mapping = {
                "humidifier": self.config["humidifier_pin"],
                "fan": self.config["fan_pin"],
                "heater": self.config["heater_pin"],
                "water_pump": self.config["water_pump_pin"]
            }
            
            if device_name not in pin_mapping:
                logger.error(f"Unknown device: {device_name}")
                return False
            
            pin = pin_mapping[device_name]
            
            if self.simulation_mode:
                self._simulate_device_control(device_name, state)
            else:
                # Relays are typically active LOW (False = ON, True = OFF)
                gpio_state = not state
                GPIO.output(pin, gpio_state)
            
            # Update device state
            self.device_states[device_name] = state
            
            action = "activated" if state else "deactivated"
            logger.info(f"Device {device_name} {action}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error controlling device {device_name}: {e}")
            return False
    
    def toggle_device(self, device_name: str, state: bool) -> bool:
        """Toggle a device state (API endpoint helper)"""
        return self.activate_device(device_name, state)
    
    def water_plants(self):
        """Special watering sequence"""
        try:
            logger.info("Starting watering sequence")
            
            # Turn on water pump
            self.activate_device("water_pump", True)
            
            if self.simulation_mode:
                logger.info("Simulated watering for 30 seconds")
            else:
                # Water for 30 seconds
                time.sleep(30)
            
            # Turn off water pump
            self.activate_device("water_pump", False)
            
            logger.info("Watering sequence completed")
            
        except Exception as e:
            logger.error(f"Error in watering sequence: {e}")
    
    def _simulate_device_control(self, device_name: str, state: bool):
        """Simulate device control for testing"""
        action = "ON" if state else "OFF"
        logger.info(f"SIMULATION: {device_name.upper()} -> {action}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current automation status"""
        return {
            "simulation_mode": self.simulation_mode,
            "device_states": self.device_states.copy(),
            "active_rules": len([r for r in self.rules if r.enabled]),
            "total_rules": len(self.rules),
            "config": self.config,
            "rules": [
                {
                    "name": rule.name,
                    "enabled": rule.enabled,
                    "description": rule.description,
                    "last_triggered": rule.last_triggered,
                    "cooldown_seconds": rule.cooldown_seconds
                }
                for rule in self.rules
            ]
        }
    
    def enable_rule(self, rule_name: str) -> bool:
        """Enable a specific rule"""
        for rule in self.rules:
            if rule.name == rule_name:
                rule.enabled = True
                logger.info(f"Enabled rule: {rule_name}")
                return True
        return False
    
    def disable_rule(self, rule_name: str) -> bool:
        """Disable a specific rule"""
        for rule in self.rules:
            if rule.name == rule_name:
                rule.enabled = False
                logger.info(f"Disabled rule: {rule_name}")
                return True
        return False
    
    def emergency_stop(self):
        """Emergency stop - turn off all devices"""
        logger.warning("EMERGENCY STOP - Deactivating all devices")
        
        devices = ["humidifier", "fan", "heater", "water_pump"]
        for device in devices:
            try:
                self.activate_device(device, False)
            except Exception as e:
                logger.error(f"Error stopping {device}: {e}")
    
    def cleanup(self):
        """Clean up GPIO resources"""
        if not self.simulation_mode:
            try:
                # Turn off all devices
                self.emergency_stop()
                
                # Clean up GPIO
                GPIO.cleanup()
                logger.info("GPIO cleanup completed")
                
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")

# Legacy function for compatibility with your notes
def check_and_trigger(sensor_data):
    """Legacy function matching your notes"""
    if sensor_data["humidity"] < 40:
        print("Trigger humidifier!")
    if sensor_data["temperature"] > 30:
        print("Trigger cooling system")

# Example usage
if __name__ == "__main__":
    # Test the automation engine
    engine = AutomationEngine()
    
    try:
        # Test with sample sensor data
        sample_data = {
            "temperature": 32,
            "humidity": 35,
            "soil_moisture": 25,
            "co2": 500
        }
        
        print("Testing automation with sample data:")
        print(json.dumps(sample_data, indent=2))
        
        triggered = engine.check_and_trigger(sample_data)
        print(f"Triggered rules: {triggered}")
        
        # Show current status
        status = engine.get_status()
        print(f"\\nAutomation Status:")
        print(f"- Simulation mode: {status['simulation_mode']}")
        print(f"- Active rules: {status['active_rules']}/{status['total_rules']}")
        print(f"- Device states: {status['device_states']}")
        
    finally:
        engine.cleanup()