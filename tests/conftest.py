"""
Pytest configuration and shared fixtures for GrowWiz tests
"""

import pytest
import sys
import os
import tempfile
import json
from unittest.mock import Mock, patch
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

@pytest.fixture
def temp_database():
    """Create a temporary database file for testing"""
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db.close()
    
    yield temp_db.name
    
    # Cleanup
    if os.path.exists(temp_db.name):
        os.unlink(temp_db.name)

@pytest.fixture
def temp_config_file():
    """Create a temporary configuration file for testing"""
    config_data = {
        'server': {
            'host': '0.0.0.0',
            'port': 8000,
            'debug': False
        },
        'hardware': {
            'platform': 'raspberry_pi',
            'simulation_mode': True
        },
        'sensors': {
            'dht22_pin': 4,
            'soil_moisture_pin': 0,
            'co2_address': '0x48',
            'read_interval': 5
        },
        'thresholds': {
            'temperature': {'min': 18, 'max': 30},
            'humidity': {'min': 40, 'max': 70},
            'soil_moisture': {'min': 30, 'max': 80},
            'co2': {'min': 400, 'max': 1000}
        },
        'relay_pins': {
            'fan': 18,
            'heater': 19,
            'humidifier': 20,
            'pump': 21,
            'lights': 22,
            'co2_valve': 23
        },
        'ai': {
            'model_name': 'resnet50',
            'confidence_threshold': 0.7,
            'max_image_size': 1024
        },
        'database': {
            'path': 'data/growwiz.db',
            'backup_interval': 24
        },
        'scraping': {
            'request_delay': 1.0,
            'max_pages': 10,
            'keywords': ['cannabis', 'growing', 'hydroponics', 'nutrients']
        },
        'logging': {
            'level': 'INFO',
            'file': 'logs/growwiz.log',
            'max_size': 10485760,
            'backup_count': 5
        }
    }
    
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    json.dump(config_data, temp_file)
    temp_file.close()
    
    yield temp_file.name
    
    # Cleanup
    if os.path.exists(temp_file.name):
        os.unlink(temp_file.name)

@pytest.fixture
def sample_sensor_data():
    """Sample sensor data for testing"""
    return {
        'temperature': 25.5,
        'humidity': 45.2,
        'soil_moisture': 72.0,
        'co2': 550.0,
        'timestamp': datetime.now().isoformat()
    }

@pytest.fixture
def sample_plant_diagnosis():
    """Sample plant diagnosis data for testing"""
    return {
        'image_path': '/test/sample_plant.jpg',
        'primary_diagnosis': 'healthy',
        'confidence': 0.85,
        'predictions': [
            {'condition': 'healthy', 'confidence': 0.85},
            {'condition': 'nutrient_deficiency', 'confidence': 0.10},
            {'condition': 'overwatering', 'confidence': 0.05}
        ],
        'recommendations': [
            'Continue current care routine',
            'Monitor for any changes in leaf color',
            'Maintain current watering schedule'
        ],
        'features': {
            'brightness': 120.5,
            'contrast': 45.2,
            'green_percentage': 78.5,
            'problem_area_percentage': 5.2,
            'color_variance': 15.8
        },
        'simulation_mode': True
    }

@pytest.fixture
def sample_automation_event():
    """Sample automation event data for testing"""
    return {
        'rule_name': 'Temperature Control',
        'device': 'fan',
        'action': 'activate',
        'trigger_value': 32.0,
        'success': True
    }

@pytest.fixture
def sample_scraped_tip():
    """Sample scraped tip data for testing"""
    return {
        'url': 'http://example.com/growing-tip',
        'content': 'Maintain humidity levels between 40-60% for optimal cannabis growth',
        'relevance_score': 0.85,
        'source': 'forum'
    }

@pytest.fixture
def mock_gpio():
    """Mock GPIO module for testing"""
    with patch('RPi.GPIO') as mock_gpio:
        mock_gpio.BCM = 'BCM'
        mock_gpio.OUT = 'OUT'
        mock_gpio.IN = 'IN'
        mock_gpio.HIGH = 1
        mock_gpio.LOW = 0
        mock_gpio.PUD_UP = 'PUD_UP'
        mock_gpio.PUD_DOWN = 'PUD_DOWN'
        
        yield mock_gpio

@pytest.fixture
def mock_dht22():
    """Mock DHT22 sensor for testing"""
    with patch('Adafruit_DHT.read_retry') as mock_dht:
        # Return sample temperature and humidity
        mock_dht.return_value = (45.2, 25.5)  # humidity, temperature
        yield mock_dht

@pytest.fixture
def mock_mcp3008():
    """Mock MCP3008 ADC for testing"""
    with patch('busio.SPI') as mock_spi, \
         patch('digitalio.DigitalInOut') as mock_cs, \
         patch('adafruit_mcp3xxx.mcp3008.MCP3008') as mock_mcp:
        
        # Mock ADC channel
        mock_channel = Mock()
        mock_channel.value = 45000  # Sample ADC value
        mock_mcp.return_value.channel = mock_channel
        
        yield mock_mcp

@pytest.fixture
def mock_i2c():
    """Mock I2C bus for testing"""
    with patch('smbus2.SMBus') as mock_bus:
        # Mock I2C read operations
        mock_bus.return_value.read_i2c_block_data.return_value = [0x02, 0x30, 0x00, 0x00]
        yield mock_bus

@pytest.fixture
def test_image_file():
    """Create a test image file for plant classification"""
    from PIL import Image
    
    # Create a simple green image (simulating a plant)
    img = Image.new('RGB', (224, 224), color='green')
    
    # Save to temporary file
    temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
    img.save(temp_file.name)
    temp_file.close()
    
    yield temp_file.name
    
    # Cleanup
    if os.path.exists(temp_file.name):
        os.unlink(temp_file.name)

@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp session for web scraping tests"""
    from unittest.mock import AsyncMock
    
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value="""
    <html>
        <body>
            <div class="post">
                <p>Cannabis plants need proper lighting for healthy growth.</p>
            </div>
            <div class="comment">
                <p>Maintain temperature between 70-85°F during flowering.</p>
            </div>
        </body>
    </html>
    """)
    
    mock_session = AsyncMock()
    mock_session.get = AsyncMock(return_value=mock_response)
    
    yield mock_session

@pytest.fixture
def mock_selenium_driver():
    """Mock Selenium WebDriver for web scraping tests"""
    mock_driver = Mock()
    mock_driver.get = Mock()
    mock_driver.page_source = """
    <html>
        <body>
            <article>
                <h1>Growing Tips for Beginners</h1>
                <p>Start with quality seeds and proper soil preparation.</p>
                <p>Monitor pH levels regularly for optimal nutrient uptake.</p>
            </article>
        </body>
    </html>
    """
    mock_driver.quit = Mock()
    
    yield mock_driver

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Test markers
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "hardware: mark test as requiring hardware"
    )
    config.addinivalue_line(
        "markers", "network: mark test as requiring network access"
    )

# Skip hardware tests if not on Raspberry Pi
def pytest_collection_modifyitems(config, items):
    """Modify test collection to skip hardware tests when appropriate"""
    import platform
    
    skip_hardware = pytest.mark.skip(reason="Hardware tests require Raspberry Pi")
    skip_network = pytest.mark.skip(reason="Network tests require internet connection")
    
    for item in items:
        # Skip hardware tests if not on Raspberry Pi
        if "hardware" in item.keywords and not platform.machine().startswith('arm'):
            item.add_marker(skip_hardware)
        
        # Skip network tests if --no-network flag is used
        if "network" in item.keywords and config.getoption("--no-network", default=False):
            item.add_marker(skip_network)

def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--no-network",
        action="store_true",
        default=False,
        help="Skip tests that require network access"
    )
    parser.addoption(
        "--hardware-only",
        action="store_true",
        default=False,
        help="Run only hardware-specific tests"
    )

# Utility functions for tests
def create_test_database(db_path):
    """Create a test database with sample data"""
    from database import DatabaseManager
    
    db = DatabaseManager(db_path)
    
    # Add sample sensor readings
    sample_readings = [
        {'temperature': 25.0, 'humidity': 50.0, 'soil_moisture': 60.0, 'co2': 500.0},
        {'temperature': 26.0, 'humidity': 48.0, 'soil_moisture': 58.0, 'co2': 520.0},
        {'temperature': 24.5, 'humidity': 52.0, 'soil_moisture': 62.0, 'co2': 480.0},
    ]
    
    for reading in sample_readings:
        reading['timestamp'] = datetime.now().isoformat()
        db.store_sensor_reading(reading)
    
    return db

def assert_sensor_data_valid(sensor_data):
    """Assert that sensor data has valid structure and values"""
    assert isinstance(sensor_data, dict)
    
    required_fields = ['temperature', 'humidity', 'soil_moisture', 'co2']
    for field in required_fields:
        assert field in sensor_data
        assert isinstance(sensor_data[field], (int, float))
    
    # Check reasonable ranges
    assert -10 <= sensor_data['temperature'] <= 50  # Celsius
    assert 0 <= sensor_data['humidity'] <= 100      # Percentage
    assert 0 <= sensor_data['soil_moisture'] <= 100 # Percentage
    assert 0 <= sensor_data['co2'] <= 5000          # PPM

def assert_diagnosis_valid(diagnosis):
    """Assert that plant diagnosis has valid structure"""
    assert isinstance(diagnosis, dict)
    
    if not diagnosis.get('error'):
        required_fields = [
            'image_path', 'primary_diagnosis', 'confidence',
            'predictions', 'recommendations'
        ]
        
        for field in required_fields:
            assert field in diagnosis
        
        assert isinstance(diagnosis['confidence'], (int, float))
        assert 0 <= diagnosis['confidence'] <= 1
        assert isinstance(diagnosis['predictions'], list)
        assert isinstance(diagnosis['recommendations'], list)

def assert_automation_event_valid(event):
    """Assert that automation event has valid structure"""
    assert isinstance(event, dict)
    
    required_fields = ['rule_name', 'device', 'action', 'success']
    for field in required_fields:
        assert field in event
    
    assert isinstance(event['success'], bool)
    assert event['action'] in ['activate', 'deactivate', 'emergency_stop']

# Custom assertions
class CustomAssertions:
    """Custom assertion methods for GrowWiz tests"""
    
    @staticmethod
    def assert_database_stats_valid(stats):
        """Assert database statistics are valid"""
        assert isinstance(stats, dict)
        
        expected_tables = [
            'sensor_readings', 'plant_diagnoses', 'automation_events',
            'system_logs', 'scraped_tips', 'user_queries'
        ]
        
        for table in expected_tables:
            assert table in stats
            assert isinstance(stats[table], int)
            assert stats[table] >= 0
    
    @staticmethod
    def assert_device_states_valid(states):
        """Assert device states are valid"""
        assert isinstance(states, dict)
        
        for device, state in states.items():
            assert isinstance(device, str)
            assert isinstance(state, bool)
    
    @staticmethod
    def assert_scraped_tip_valid(tip):
        """Assert scraped tip has valid structure"""
        assert isinstance(tip, dict)
        
        required_fields = ['url', 'content', 'relevance_score', 'source']
        for field in required_fields:
            assert field in tip
        
        assert isinstance(tip['relevance_score'], (int, float))
        assert 0 <= tip['relevance_score'] <= 1
        assert tip['source'] in ['forum', 'blog', 'article']

# Make custom assertions available to all tests
@pytest.fixture
def custom_assert():
    """Provide custom assertion methods"""
    return CustomAssertions()