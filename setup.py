"""
Setup script for GrowWiz - AI-assisted grow room management system
"""

from setuptools import setup, find_packages
import os
import sys

# Read the README file
def read_readme():
    """Read README.md file for long description"""
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "AI-assisted grow room management system with sensor monitoring, plant diagnosis, and automation."

# Read requirements from requirements.txt
def read_requirements():
    """Read requirements from requirements.txt"""
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    requirements = []
    
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip comments, empty lines, and built-in modules
                if (line and not line.startswith('#') and 
                    not line.startswith('sqlite3') and
                    ';' not in line):  # Skip platform-specific requirements
                    requirements.append(line)
    
    return requirements

# Platform-specific requirements
def get_platform_requirements():
    """Get platform-specific requirements"""
    platform_reqs = []
    
    # Raspberry Pi specific packages
    if sys.platform.startswith('linux') and (
        'arm' in os.uname().machine or 'aarch64' in os.uname().machine
    ):
        platform_reqs.extend([
            'RPi.GPIO>=0.7.1',
            'adafruit-circuitpython-dht>=3.7.9',
            'smbus2>=0.4.2',
            'netifaces>=0.11.0'
        ])
    
    return platform_reqs

# Get version from src/__init__.py or set default
def get_version():
    """Get version from package or set default"""
    version_file = os.path.join(os.path.dirname(__file__), 'src', '__init__.py')
    if os.path.exists(version_file):
        with open(version_file, 'r') as f:
            for line in f:
                if line.startswith('__version__'):
                    return line.split('=')[1].strip().strip('"\'')
    return '1.0.0'

setup(
    name='growwiz',
    version=get_version(),
    author='Chris',
    author_email='chris@example.com',
    description='AI-assisted grow room management system',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/chris/growwiz',
    project_urls={
        'Bug Reports': 'https://github.com/chris/growwiz/issues',
        'Source': 'https://github.com/chris/growwiz',
        'Documentation': 'https://github.com/chris/growwiz/wiki',
    },
    
    # Package configuration
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    package_data={
        'growwiz': [
            'static/*',
            'templates/*',
            'data/*',
            'models/*',
        ],
    },
    
    # Requirements
    python_requires='>=3.8',
    install_requires=read_requirements() + get_platform_requirements(),
    
    # Optional dependencies
    extras_require={
        'dev': [
            'pytest>=7.4.3',
            'pytest-asyncio>=0.21.1',
            'pytest-mock>=3.12.0',
            'pytest-cov>=4.1.0',
            'pytest-xdist>=3.5.0',
            'pytest-timeout>=2.2.0',
            'black>=23.11.0',
            'flake8>=6.1.0',
            'isort>=5.12.0',
            'mypy>=1.7.1',
            'pre-commit>=3.6.0',
        ],
        'docs': [
            'mkdocs>=1.5.3',
            'mkdocs-material>=9.4.8',
            'sphinx>=7.2.6',
        ],
        'monitoring': [
            'prometheus-client>=0.19.0',
            'grafana-api>=1.0.3',
        ],
        'cloud': [
            'boto3>=1.34.0',
            'google-cloud-storage>=2.10.0',
        ],
        'ml': [
            'tensorflow>=2.13.0',
            'onnx>=1.15.0',
            'onnxruntime>=1.16.3',
            'mlflow>=2.8.1',
        ],
        'production': [
            'supervisor>=4.2.5',
            'gunicorn>=21.2.0',
            'nginx',  # Note: This would need to be installed separately
        ],
        'all': [
            # Include all optional dependencies
        ],
    },
    
    # Entry points for command-line scripts
    entry_points={
        'console_scripts': [
            'growwiz=cli:main',
            'growwiz-server=server:main',
            'growwiz-monitor=cli:monitor_command',
            'growwiz-diagnose=cli:diagnose_command',
            'growwiz-scrape=cli:scrape_command',
        ],
    },
    
    # Classification
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Home Automation',
        'Topic :: System :: Monitoring',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
        'Operating System :: POSIX :: Linux',  # Raspberry Pi support
        'Environment :: Web Environment',
        'Framework :: FastAPI',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],
    
    # Keywords
    keywords=[
        'agriculture', 'automation', 'ai', 'machine-learning',
        'raspberry-pi', 'sensors', 'monitoring', 'hydroponics',
        'growing', 'plant-care', 'iot', 'smart-home'
    ],
    
    # License
    license='MIT',
    
    # Zip safe
    zip_safe=False,
    
    # Platform requirements
    platforms=['any'],
    
    # Additional metadata
    maintainer='Chris',
    maintainer_email='chris@example.com',
    
    # Test suite
    test_suite='tests',
    tests_require=[
        'pytest>=7.4.3',
        'pytest-asyncio>=0.21.1',
        'pytest-mock>=3.12.0',
        'pytest-cov>=4.1.0',
    ],
    
    # Command options
    options={
        'build_scripts': {
            'executable': '/usr/bin/python3',
        },
    },
)

# Post-installation setup
def post_install():
    """Post-installation setup tasks"""
    import os
    import stat
    
    # Create necessary directories
    directories = [
        'data',
        'logs',
        'models',
        'backups',
        'uploads',
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Set permissions for log directory
    if os.path.exists('logs'):
        os.chmod('logs', stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP)
    
    # Create default configuration file if it doesn't exist
    config_file = '.env'
    if not os.path.exists(config_file):
        default_config = """# GrowWiz Configuration
# Server settings
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Hardware settings
HARDWARE_PLATFORM=raspberry_pi
SIMULATION_MODE=true

# Sensor settings
DHT22_PIN=4
SOIL_MOISTURE_PIN=0
CO2_ADDRESS=0x48
READ_INTERVAL=5

# Thresholds
TEMP_MIN=18
TEMP_MAX=30
HUMIDITY_MIN=40
HUMIDITY_MAX=70
SOIL_MOISTURE_MIN=30
SOIL_MOISTURE_MAX=80
CO2_MIN=400
CO2_MAX=1000

# Relay pins
FAN_PIN=18
HEATER_PIN=19
HUMIDIFIER_PIN=20
PUMP_PIN=21
LIGHTS_PIN=22
CO2_VALVE_PIN=23

# AI settings
MODEL_NAME=resnet50
CONFIDENCE_THRESHOLD=0.7
MAX_IMAGE_SIZE=1024

# Database
DATABASE_PATH=data/growwiz.db
BACKUP_INTERVAL=24

# Scraping
REQUEST_DELAY=1.0
MAX_PAGES=10

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/growwiz.log
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5
"""
        with open(config_file, 'w') as f:
            f.write(default_config)
        print(f"Created default configuration: {config_file}")
    
    print("GrowWiz installation completed successfully!")
    print("Run 'growwiz --help' to get started.")

if __name__ == '__main__':
    # Run post-installation setup if this script is executed directly
    post_install()