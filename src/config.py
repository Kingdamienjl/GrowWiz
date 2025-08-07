"""
GrowWiz Configuration Management
Centralized configuration handling for all modules
"""

import os
import json
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

class Config:
    """Centralized configuration manager"""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration
        
        Args:
            config_file: Optional path to config file (JSON or YAML)
        """
        self.config_file = config_file
        self.config_data = {}
        
        # Load environment variables
        self._load_env()
        
        # Load config file if provided
        if config_file and os.path.exists(config_file):
            self._load_config_file(config_file)
        
        # Set up default configuration
        self._setup_defaults()
        
        logger.info(f"Configuration loaded from {config_file or 'environment'}")
    
    def _load_env(self):
        """Load environment variables from .env file"""
        env_path = Path(__file__).parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            logger.info(f"Loaded environment from {env_path}")
    
    def _load_config_file(self, config_file: str):
        """Load configuration from JSON or YAML file"""
        try:
            with open(config_file, 'r') as f:
                if config_file.endswith('.json'):
                    self.config_data = json.load(f)
                elif config_file.endswith(('.yml', '.yaml')):
                    self.config_data = yaml.safe_load(f)
                else:
                    logger.warning(f"Unsupported config file format: {config_file}")
        except Exception as e:
            logger.error(f"Error loading config file {config_file}: {e}")
    
    def _setup_defaults(self):
        """Set up default configuration values"""
        self.defaults = {
            # Server settings
            'server': {
                'host': '0.0.0.0',
                'port': 8000,
                'debug': False,
                'reload': False
            },
            
            # Hardware settings
            'hardware': {
                'platform': 'raspberry_pi',
                'simulation_mode': True,
                'gpio_cleanup': True
            },
            
            # Sensor settings
            'sensors': {
                'dht22_pin': 4,
                'soil_moisture_pin': 0,
                'co2_i2c_address': '0x61',
                'reading_interval': 60,
                'max_retries': 3,
                'retry_delay': 1.0
            },
            
            # Sensor thresholds
            'thresholds': {
                'temperature': {
                    'min': 18.0,
                    'max': 28.0,
                    'critical_min': 15.0,
                    'critical_max': 35.0
                },
                'humidity': {
                    'min': 40.0,
                    'max': 60.0,
                    'critical_min': 30.0,
                    'critical_max': 80.0
                },
                'soil_moisture': {
                    'min': 30.0,
                    'max': 70.0,
                    'critical_min': 20.0,
                    'critical_max': 90.0
                },
                'co2': {
                    'min': 400.0,
                    'max': 1200.0,
                    'critical_min': 300.0,
                    'critical_max': 2000.0
                }
            },
            
            # Automation relay pins
            'relays': {
                'fan': 18,
                'heater': 19,
                'humidifier': 20,
                'dehumidifier': 21,
                'water_pump': 22,
                'co2_valve': 23,
                'lights': 24,
                'exhaust_fan': 25
            },
            
            # AI model settings
            'ai': {
                'model_name': 'resnet50',
                'model_path': './models/',
                'confidence_threshold': 0.7,
                'max_image_size': 1024,
                'simulation_mode': True
            },
            
            # Database settings
            'database': {
                'path': './data/growwiz.db',
                'backup_interval': 86400,  # 24 hours
                'cleanup_days': 30,
                'max_size_mb': 100
            },
            
            # Scraping settings
            'scraping': {
                'max_pages': 50,
                'delay_between_requests': 2.0,
                'timeout': 30,
                'user_agent': 'GrowWiz Bot 1.0',
                'max_content_length': 10000,
                'keywords': [
                    'cannabis', 'marijuana', 'grow', 'cultivation',
                    'nutrients', 'lighting', 'humidity', 'temperature',
                    'harvest', 'flowering', 'vegetative', 'seedling'
                ]
            },
            
            # Logging settings
            'logging': {
                'level': 'INFO',
                'file': './logs/growwiz.log',
                'max_size': '10 MB',
                'retention': '30 days',
                'format': '{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}'
            },
            
            # API settings
            'api': {
                'rate_limit': 100,  # requests per minute
                'cors_origins': ['*'],
                'docs_url': '/docs',
                'redoc_url': '/redoc'
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation
        
        Args:
            key: Configuration key (e.g., 'sensors.dht22_pin')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        # Check environment variables first
        env_key = key.upper().replace('.', '_')
        env_value = os.getenv(env_key)
        if env_value is not None:
            return self._convert_env_value(env_value)
        
        # Check config file data
        value = self._get_nested_value(self.config_data, key)
        if value is not None:
            return value
        
        # Check defaults
        value = self._get_nested_value(self.defaults, key)
        if value is not None:
            return value
        
        return default
    
    def _get_nested_value(self, data: Dict[str, Any], key: str) -> Any:
        """Get nested dictionary value using dot notation"""
        keys = key.split('.')
        current = data
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None
        
        return current
    
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type"""
        # Boolean conversion
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Number conversion
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # JSON conversion
        if value.startswith(('{', '[')):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value using dot notation"""
        keys = key.split('.')
        current = self.config_data
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        return self.get(section, {})
    
    def save_config(self, config_file: Optional[str] = None):
        """Save current configuration to file"""
        file_path = config_file or self.config_file
        if not file_path:
            raise ValueError("No config file specified")
        
        try:
            with open(file_path, 'w') as f:
                if file_path.endswith('.json'):
                    json.dump(self.config_data, f, indent=2)
                elif file_path.endswith(('.yml', '.yaml')):
                    yaml.dump(self.config_data, f, default_flow_style=False)
            
            logger.info(f"Configuration saved to {file_path}")
        except Exception as e:
            logger.error(f"Error saving config to {file_path}: {e}")
            raise
    
    def validate_config(self) -> Dict[str, list]:
        """Validate configuration and return any issues"""
        issues = {
            'errors': [],
            'warnings': []
        }
        
        # Validate sensor pins
        sensor_pins = [
            self.get('sensors.dht22_pin'),
            self.get('relays.fan'),
            self.get('relays.heater'),
            self.get('relays.humidifier')
        ]
        
        # Check for duplicate pins
        used_pins = [pin for pin in sensor_pins if pin is not None]
        if len(used_pins) != len(set(used_pins)):
            issues['errors'].append("Duplicate GPIO pins detected")
        
        # Validate thresholds
        for sensor in ['temperature', 'humidity', 'soil_moisture', 'co2']:
            min_val = self.get(f'thresholds.{sensor}.min')
            max_val = self.get(f'thresholds.{sensor}.max')
            
            if min_val is not None and max_val is not None and min_val >= max_val:
                issues['errors'].append(f"Invalid {sensor} threshold: min >= max")
        
        # Validate paths
        db_path = Path(self.get('database.path')).parent
        if not db_path.exists():
            issues['warnings'].append(f"Database directory does not exist: {db_path}")
        
        model_path = Path(self.get('ai.model_path'))
        if not model_path.exists():
            issues['warnings'].append(f"AI model directory does not exist: {model_path}")
        
        return issues
    
    def get_sensor_config(self) -> Dict[str, Any]:
        """Get sensor-specific configuration"""
        return {
            'pins': self.get_section('sensors'),
            'thresholds': self.get_section('thresholds'),
            'reading_interval': self.get('sensors.reading_interval', 60),
            'max_retries': self.get('sensors.max_retries', 3),
            'retry_delay': self.get('sensors.retry_delay', 1.0),
            'simulation_mode': self.get('hardware.simulation_mode', True)
        }
    
    @property
    def environment(self):
        """Get current environment"""
        env_value = self.get('environment', 'development')
        if hasattr(self, '_environment_enum'):
            return self._environment_enum(env_value)
        return env_value
    
    def is_testing_mode(self) -> bool:
        """Check if running in testing mode"""
        return self.get('environment', 'DEVELOPMENT').upper() == 'TESTING'
    
    def is_production_mode(self) -> bool:
        """Check if running in production mode"""
        return self.get('environment', 'DEVELOPMENT').upper() == 'PRODUCTION'
    
    def is_simulation_mode(self) -> bool:
        """Check if running in simulation mode"""
        return self.get('hardware.simulation_mode', True) or self.get('force_simulation', False)
    
    def get_ai_config(self) -> Dict[str, Any]:
        """Get AI-specific configuration"""
        return self.get_section('ai')
    
    def get_scraping_config(self) -> Dict[str, Any]:
        """Get scraping-specific configuration"""
        return {
            "max_concurrent": int(os.getenv("MAX_CONCURRENT_SCRAPES", "5")),
            "request_delay": float(os.getenv("REQUEST_DELAY", "1.0")),
            "timeout": int(os.getenv("SCRAPE_TIMEOUT", "30")),
            "user_agent": os.getenv("USER_AGENT", "GrowWiz/1.0 (+https://growwiz.ai)"),
            "respect_robots": os.getenv("RESPECT_ROBOTS", "true").lower() == "true"
        }
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database-specific configuration"""
        return self.get_section('database')
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging-specific configuration"""
        return self.get_section('logging')
    
    def __str__(self) -> str:
        """String representation of configuration"""
        return f"GrowWiz Config (file: {self.config_file or 'env only'})"
    
    def __repr__(self) -> str:
        return self.__str__()

# Global configuration instance
config = Config()

# Convenience functions
def get_config(key: str, default: Any = None) -> Any:
    """Get configuration value"""
    return config.get(key, default)

def get_section(section: str) -> Dict[str, Any]:
    """Get configuration section"""
    return config.get_section(section)

def set_config(key: str, value: Any):
    """Set configuration value"""
    config.set(key, value)

def load_config_file(config_file: str):
    """Load configuration from file"""
    global config
    config = Config(config_file)

def validate_config() -> Dict[str, list]:
    """Validate current configuration"""
    return config.validate_config()

# Example usage
if __name__ == "__main__":
    # Test configuration
    print("GrowWiz Configuration Test")
    print("=" * 40)
    
    # Test basic gets
    print(f"Server host: {get_config('server.host')}")
    print(f"DHT22 pin: {get_config('sensors.dht22_pin')}")
    print(f"Temperature min: {get_config('thresholds.temperature.min')}")
    
    # Test section get
    sensor_config = get_section('sensors')
    print(f"Sensor config: {sensor_config}")
    
    # Test validation
    issues = validate_config()
    if issues['errors']:
        print(f"Configuration errors: {issues['errors']}")
    if issues['warnings']:
        print(f"Configuration warnings: {issues['warnings']}")
    
    print("Configuration test completed!")