"""
GrowWiz - AI-assisted grow room management system

A comprehensive solution for monitoring and automating grow room environments
using Raspberry Pi sensors, AI-powered plant diagnosis, and web-scraped advice.

Author: Chris
License: MIT
"""

__version__ = '1.0.0'
__author__ = 'Chris'
__email__ = 'chris@example.com'
__license__ = 'MIT'
__description__ = 'AI-assisted grow room management system'

# Import main modules for easy access
try:
    from .sensors import SensorManager
    from .plant_classifier import PlantClassifier
    from .scraper import GrowTipScraper
    from .automation import AutomationEngine
    from .database import DatabaseManager
    from .config import Config
    from .utils import (
        get_timestamp, format_timestamp, clean_text,
        validate_sensor_data, is_raspberry_pi, RateLimiter
    )
    
    # Define what gets imported with "from growwiz import *"
    __all__ = [
        'SensorManager',
        'PlantClassifier', 
        'GrowTipScraper',
        'AutomationEngine',
        'DatabaseManager',
        'Config',
        'get_timestamp',
        'format_timestamp',
        'clean_text',
        'validate_sensor_data',
        'is_raspberry_pi',
        'RateLimiter',
    ]
    
except ImportError as e:
    # Handle missing dependencies gracefully
    import warnings
    warnings.warn(f"Some GrowWiz modules could not be imported: {e}")
    __all__ = []

# Package metadata
__package_info__ = {
    'name': 'growwiz',
    'version': __version__,
    'author': __author__,
    'email': __email__,
    'license': __license__,
    'description': __description__,
    'url': 'https://github.com/chris/growwiz',
    'keywords': [
        'agriculture', 'automation', 'ai', 'machine-learning',
        'raspberry-pi', 'sensors', 'monitoring', 'hydroponics',
        'growing', 'plant-care', 'iot', 'smart-home'
    ],
    'classifiers': [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Home Automation',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ]
}

def get_version():
    """Get the current version of GrowWiz"""
    return __version__

def get_package_info():
    """Get package information dictionary"""
    return __package_info__.copy()

def check_dependencies():
    """Check if all required dependencies are available"""
    missing_deps = []
    optional_deps = []
    
    # Core dependencies
    core_deps = [
        ('fastapi', 'FastAPI web framework'),
        ('uvicorn', 'ASGI server'),
        ('pydantic', 'Data validation'),
        ('sqlite3', 'Database support'),
        ('PIL', 'Image processing'),
        ('numpy', 'Numerical computing'),
        ('requests', 'HTTP client'),
        ('beautifulsoup4', 'HTML parsing'),
    ]
    
    # Optional dependencies
    opt_deps = [
        ('RPi.GPIO', 'Raspberry Pi GPIO control'),
        ('Adafruit_DHT', 'DHT sensor support'),
        ('smbus2', 'I2C communication'),
        ('selenium', 'Web scraping with browser'),
        ('torch', 'PyTorch ML framework'),
        ('tensorflow', 'TensorFlow ML framework'),
    ]
    
    # Check core dependencies
    for dep, desc in core_deps:
        try:
            __import__(dep)
        except ImportError:
            missing_deps.append((dep, desc))
    
    # Check optional dependencies
    for dep, desc in opt_deps:
        try:
            __import__(dep)
        except ImportError:
            optional_deps.append((dep, desc))
    
    return {
        'missing_required': missing_deps,
        'missing_optional': optional_deps,
        'all_satisfied': len(missing_deps) == 0
    }

def print_system_info():
    """Print system information and dependency status"""
    import sys
    import platform
    
    print(f"GrowWiz v{__version__}")
    print(f"Python {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"Architecture: {platform.machine()}")
    
    # Check dependencies
    deps = check_dependencies()
    
    if deps['all_satisfied']:
        print("✓ All required dependencies are satisfied")
    else:
        print("✗ Missing required dependencies:")
        for dep, desc in deps['missing_required']:
            print(f"  - {dep}: {desc}")
    
    if deps['missing_optional']:
        print("Optional dependencies not available:")
        for dep, desc in deps['missing_optional']:
            print(f"  - {dep}: {desc}")
    
    # Hardware detection
    try:
        from .utils import is_raspberry_pi, get_system_info
        if is_raspberry_pi():
            print("✓ Running on Raspberry Pi")
            sys_info = get_system_info()
            print(f"  CPU: {sys_info.get('cpu', 'Unknown')}")
            print(f"  Memory: {sys_info.get('memory', 'Unknown')}")
        else:
            print("Running on non-Raspberry Pi system (simulation mode recommended)")
    except ImportError:
        print("Could not detect hardware information")

# Module initialization
def initialize():
    """Initialize the GrowWiz package"""
    import os
    import logging
    
    # Create necessary directories
    directories = ['data', 'logs', 'models', 'uploads', 'backups']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    # Set up basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/growwiz.log'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger('growwiz')
    logger.info(f"GrowWiz v{__version__} initialized")
    
    return logger

# Auto-initialize when imported
try:
    _logger = initialize()
except Exception as e:
    import warnings
    warnings.warn(f"GrowWiz initialization failed: {e}")

# Convenience functions for quick access
def quick_sensor_reading():
    """Get a quick sensor reading (simulation mode if hardware not available)"""
    try:
        from .sensors import SensorManager
        sensor_manager = SensorManager()
        return sensor_manager.read_all_sensors()
    except Exception as e:
        return {'error': str(e)}

def quick_plant_diagnosis(image_path):
    """Get a quick plant diagnosis from an image"""
    try:
        from .plant_classifier import PlantClassifier
        classifier = PlantClassifier()
        return classifier.classify_plant(image_path)
    except Exception as e:
        return {'error': str(e)}

def quick_automation_check(sensor_data):
    """Perform a quick automation check with sensor data"""
    try:
        from .automation import AutomationEngine
        automation = AutomationEngine()
        return automation.check_and_trigger(sensor_data)
    except Exception as e:
        return {'error': str(e)}

# Add convenience functions to __all__
__all__.extend([
    'get_version',
    'get_package_info', 
    'check_dependencies',
    'print_system_info',
    'quick_sensor_reading',
    'quick_plant_diagnosis',
    'quick_automation_check'
])

# Package-level configuration
DEFAULT_CONFIG = {
    'simulation_mode': True,
    'debug': False,
    'log_level': 'INFO',
    'database_path': 'data/growwiz.db',
    'model_path': 'models/',
    'upload_path': 'uploads/',
    'backup_path': 'backups/',
}

def get_default_config():
    """Get default configuration dictionary"""
    return DEFAULT_CONFIG.copy()

# Export default config
__all__.append('get_default_config')