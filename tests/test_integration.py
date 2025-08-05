"""
Integration tests for GrowWiz system
Tests the interaction between different modules
"""

import pytest
import sys
import os
import tempfile
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sensors import SensorManager
from plant_classifier import PlantClassifier
from scraper import GrowTipScraper
from automation import AutomationEngine
from database import DatabaseManager
from config import ConfigManager
from utils import get_timestamp

class TestSystemIntegration:
    """Test integration between all major components"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        # Initialize components
        self.db = DatabaseManager(self.temp_db.name)
        self.sensors = SensorManager()
        self.classifier = PlantClassifier()
        self.automation = AutomationEngine()
        self.scraper = GrowTipScraper()
        
        # Sample data
        self.sample_sensor_data = {
            'temperature': 28.5,
            'humidity': 42.0,
            'soil_moisture': 55.0,
            'co2': 480.0
        }
    
    def teardown_method(self):
        """Clean up after tests"""
        if hasattr(self.db, 'close'):
            self.db.close()
        
        if hasattr(self.automation, 'cleanup'):
            self.automation.cleanup()
        
        # Clean up scraper
        if hasattr(self.scraper, 'close'):
            asyncio.run(self.scraper.close())
        
        # Remove temporary database
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_sensor_to_database_integration(self):
        """Test sensor data flow to database"""
        # Read sensor data
        sensor_data = self.sensors.read_all_sensors()
        
        # Store in database
        reading_id = self.db.store_sensor_reading(sensor_data)
        
        assert reading_id is not None
        
        # Retrieve and verify
        readings = self.db.get_sensor_readings(limit=1)
        assert len(readings) == 1
        assert readings[0]['temperature'] == sensor_data['temperature']
        assert readings[0]['humidity'] == sensor_data['humidity']
    
    def test_sensor_to_automation_integration(self):
        """Test sensor data triggering automation"""
        # Setup automation rules
        self.automation._setup_default_rules()
        
        # Create sensor data that should trigger automation
        trigger_data = {
            'temperature': 35.0,  # High temperature
            'humidity': 25.0,     # Low humidity
            'soil_moisture': 20.0, # Low soil moisture
            'co2': 300.0,         # Low CO2
            'timestamp': get_timestamp()
        }
        
        # Process sensor data through automation
        result = self.automation.process_sensor_data(trigger_data)
        
        assert isinstance(result, dict)
        assert 'triggered_actions' in result
        assert len(result['triggered_actions']) > 0
        
        # Store automation events in database
        for action in result['triggered_actions']:
            event_data = {
                'rule_name': action['rule_name'],
                'device': action['device'],
                'action': action['action'],
                'trigger_value': trigger_data.get(action.get('sensor', 'temperature'), 0),
                'success': True
            }
            event_id = self.db.store_automation_event(event_data)
            assert event_id is not None
    
    def test_plant_diagnosis_to_database_integration(self):
        """Test plant diagnosis storage in database"""
        # Create test image
        test_image = self._create_test_image()
        
        try:
            # Classify plant
            diagnosis = self.classifier.classify_image(test_image)
            
            if not diagnosis.get('error'):
                # Store diagnosis in database
                diagnosis_id = self.db.store_plant_diagnosis(diagnosis)
                
                assert diagnosis_id is not None
                
                # Retrieve and verify
                diagnoses = self.db.get_plant_diagnoses(limit=1)
                assert len(diagnoses) == 1
                assert diagnoses[0]['primary_diagnosis'] == diagnosis['primary_diagnosis']
                assert diagnoses[0]['confidence'] == diagnosis['confidence']
        
        finally:
            if os.path.exists(test_image):
                os.unlink(test_image)
    
    @pytest.mark.asyncio
    async def test_scraper_to_database_integration(self):
        """Test scraped data storage in database"""
        # Mock scraper response
        mock_response = AsyncMock()
        mock_response.text = AsyncMock(return_value="""
        <html>
            <body>
                <div class="post">
                    <p>Cannabis plants need proper ventilation for healthy growth.</p>
                </div>
            </body>
        </html>
        """)
        mock_response.status = 200
        
        mock_session = AsyncMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        self.scraper.session = mock_session
        
        # Override config for testing
        self.scraper.config['target_sites'] = {
            'forums': ['http://test-forum.com'],
            'blogs': []
        }
        
        # Scrape data
        scraped_data = await self.scraper.scrape_all()
        
        # Store scraped tips in database
        for tip in scraped_data:
            tip_data = {
                'url': tip['url'],
                'content': tip['content'],
                'relevance_score': tip['relevance_score'],
                'source': 'forum'
            }
            tip_id = self.db.store_scraped_tip(tip_data)
            assert tip_id is not None
        
        # Verify storage
        tips = self.db.get_scraped_tips()
        assert len(tips) > 0
    
    def test_complete_monitoring_cycle(self):
        """Test complete monitoring and response cycle"""
        # 1. Read sensors
        sensor_data = self.sensors.read_all_sensors()
        sensor_data['timestamp'] = get_timestamp()
        
        # 2. Store sensor data
        reading_id = self.db.store_sensor_reading(sensor_data)
        assert reading_id is not None
        
        # 3. Check automation rules
        automation_result = self.automation.process_sensor_data(sensor_data)
        
        # 4. Store automation events
        for action in automation_result['triggered_actions']:
            event_data = {
                'rule_name': action['rule_name'],
                'device': action['device'],
                'action': action['action'],
                'trigger_value': sensor_data.get('temperature', 0),
                'success': True
            }
            event_id = self.db.store_automation_event(event_data)
            assert event_id is not None
        
        # 5. Log system activity
        log_data = {
            'level': 'INFO',
            'message': f'Monitoring cycle completed. {len(automation_result["triggered_actions"])} actions triggered.',
            'module': 'integration_test'
        }
        log_id = self.db.store_system_log(log_data)
        assert log_id is not None
        
        # 6. Verify data integrity
        stats = self.db.get_database_stats()
        assert stats['sensor_readings'] >= 1
        assert stats['automation_events'] >= 0
        assert stats['system_logs'] >= 1
    
    def test_ai_advice_integration(self):
        """Test AI advice generation using multiple data sources"""
        # Store some sensor data
        sensor_data = self.sample_sensor_data.copy()
        sensor_data['timestamp'] = get_timestamp()
        self.db.store_sensor_reading(sensor_data)
        
        # Store some scraped tips
        tips_data = [
            {
                'url': 'http://example.com/tip1',
                'content': 'Maintain temperature between 70-85°F for optimal growth',
                'relevance_score': 0.9,
                'source': 'forum'
            },
            {
                'url': 'http://example.com/tip2',
                'content': 'Low humidity can cause leaf curling and slow growth',
                'relevance_score': 0.8,
                'source': 'blog'
            }
        ]
        
        for tip in tips_data:
            self.db.store_scraped_tip(tip)
        
        # Simulate AI advice generation
        user_query = "My plants look stressed, what should I do?"
        
        # Get current sensor data
        recent_readings = self.db.get_sensor_readings(limit=1)
        
        # Get relevant tips
        relevant_tips = self.db.search_tips('stress')
        if not relevant_tips:
            relevant_tips = self.db.get_scraped_tips(limit=3)
        
        # Generate advice context
        advice_context = {
            'query': user_query,
            'current_conditions': recent_readings[0] if recent_readings else None,
            'relevant_tips': relevant_tips,
            'timestamp': get_timestamp()
        }
        
        # Store user query
        query_data = {
            'query': user_query,
            'response': 'Based on current conditions and expert tips, check temperature and humidity levels.',
            'context': json.dumps(advice_context)
        }
        query_id = self.db.store_user_query(query_data)
        assert query_id is not None
    
    def test_emergency_response_integration(self):
        """Test emergency response across all systems"""
        # Create emergency conditions
        emergency_data = {
            'temperature': 45.0,  # Dangerously high
            'humidity': 95.0,     # Dangerously high
            'soil_moisture': 10.0, # Critically low
            'co2': 2000.0,        # Dangerously high
            'timestamp': get_timestamp()
        }
        
        # 1. Store emergency sensor reading
        reading_id = self.db.store_sensor_reading(emergency_data)
        assert reading_id is not None
        
        # 2. Process through automation (should trigger emergency actions)
        automation_result = self.automation.process_sensor_data(emergency_data)
        
        # Should trigger multiple emergency actions
        assert len(automation_result['triggered_actions']) > 0
        
        # 3. Store all automation events
        for action in automation_result['triggered_actions']:
            event_data = {
                'rule_name': action['rule_name'],
                'device': action['device'],
                'action': action['action'],
                'trigger_value': emergency_data.get('temperature', 0),
                'success': True
            }
            self.db.store_automation_event(event_data)
        
        # 4. Log emergency
        emergency_log = {
            'level': 'CRITICAL',
            'message': f'Emergency conditions detected: Temp={emergency_data["temperature"]}°C, Humidity={emergency_data["humidity"]}%',
            'module': 'emergency_response'
        }
        self.db.store_system_log(emergency_log)
        
        # 5. Trigger emergency stop
        emergency_stop_result = self.automation.emergency_stop()
        assert emergency_stop_result is True
        
        # 6. Verify all devices are off
        device_states = self.automation.get_all_device_states()
        for device, state in device_states.items():
            assert state is False
    
    def test_data_persistence_and_recovery(self):
        """Test data persistence and system recovery"""
        # Store various types of data
        sensor_data = self.sample_sensor_data.copy()
        sensor_data['timestamp'] = get_timestamp()
        
        sensor_id = self.db.store_sensor_reading(sensor_data)
        
        # Create and store plant diagnosis
        test_image = self._create_test_image()
        try:
            diagnosis = self.classifier.classify_image(test_image)
            if not diagnosis.get('error'):
                diagnosis_id = self.db.store_plant_diagnosis(diagnosis)
        finally:
            if os.path.exists(test_image):
                os.unlink(test_image)
        
        # Store automation event
        event_data = {
            'rule_name': 'Test Rule',
            'device': 'fan',
            'action': 'activate',
            'trigger_value': 30.0,
            'success': True
        }
        event_id = self.db.store_automation_event(event_data)
        
        # Close database connection
        self.db.close()
        
        # Recreate database manager (simulating system restart)
        new_db = DatabaseManager(self.temp_db.name)
        
        try:
            # Verify data persistence
            readings = new_db.get_sensor_readings()
            assert len(readings) >= 1
            
            events = new_db.get_automation_events()
            assert len(events) >= 1
            
            # Verify database stats
            stats = new_db.get_database_stats()
            assert stats['sensor_readings'] >= 1
            assert stats['automation_events'] >= 1
            
        finally:
            new_db.close()
    
    def test_configuration_integration(self):
        """Test configuration management across modules"""
        # Create temporary config file
        config_data = {
            'sensors': {
                'dht22_pin': 4,
                'soil_moisture_pin': 0,
                'simulation_mode': True
            },
            'automation': {
                'thresholds': {
                    'temperature': {'min': 18, 'max': 30},
                    'humidity': {'min': 40, 'max': 70}
                }
            },
            'database': {
                'path': self.temp_db.name
            }
        }
        
        config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(config_data, config_file)
        config_file.close()
        
        try:
            # Load configuration
            config_manager = ConfigManager(config_file.name)
            
            # Verify configuration is loaded correctly
            sensor_config = config_manager.get('sensors', {})
            assert sensor_config['dht22_pin'] == 4
            assert sensor_config['simulation_mode'] is True
            
            automation_config = config_manager.get('automation', {})
            assert automation_config['thresholds']['temperature']['max'] == 30
            
        finally:
            os.unlink(config_file.name)
    
    def test_performance_under_load(self):
        """Test system performance under load"""
        import time
        
        start_time = time.time()
        
        # Simulate high-frequency sensor readings
        for i in range(10):
            sensor_data = self.sample_sensor_data.copy()
            sensor_data['temperature'] += i * 0.1
            sensor_data['timestamp'] = get_timestamp()
            
            # Store sensor data
            self.db.store_sensor_reading(sensor_data)
            
            # Process through automation
            self.automation.process_sensor_data(sensor_data)
        
        end_time = time.time()
        
        # Should complete in reasonable time
        assert (end_time - start_time) < 5.0  # Less than 5 seconds
        
        # Verify all data was stored
        readings = self.db.get_sensor_readings()
        assert len(readings) >= 10
    
    def _create_test_image(self):
        """Create a test image file for plant classification"""
        from PIL import Image
        
        # Create a simple green image
        img = Image.new('RGB', (224, 224), color='green')
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        img.save(temp_file.name)
        temp_file.close()
        
        return temp_file.name

class TestAPIIntegration:
    """Test API integration with backend modules"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        # Initialize components
        self.db = DatabaseManager(self.temp_db.name)
        self.sensors = SensorManager()
        self.automation = AutomationEngine()
    
    def teardown_method(self):
        """Clean up after tests"""
        if hasattr(self.db, 'close'):
            self.db.close()
        
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_sensor_api_integration(self):
        """Test sensor data API integration"""
        # Simulate API endpoint behavior
        def get_sensor_data():
            """Simulate /api/sensors endpoint"""
            try:
                sensor_data = self.sensors.read_all_sensors()
                sensor_data['timestamp'] = get_timestamp()
                
                # Store in database
                self.db.store_sensor_reading(sensor_data)
                
                return {
                    'success': True,
                    'data': sensor_data,
                    'timestamp': sensor_data['timestamp']
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'timestamp': get_timestamp()
                }
        
        # Test API endpoint
        response = get_sensor_data()
        
        assert response['success'] is True
        assert 'data' in response
        assert 'temperature' in response['data']
        assert 'humidity' in response['data']
        assert 'timestamp' in response
    
    def test_automation_api_integration(self):
        """Test automation control API integration"""
        # Setup automation
        self.automation._setup_default_rules()
        
        def control_device(device, state):
            """Simulate /api/automation/control endpoint"""
            try:
                result = self.automation.activate_device(device, state)
                
                # Log the action
                event_data = {
                    'rule_name': 'Manual Control',
                    'device': device,
                    'action': 'activate' if state else 'deactivate',
                    'trigger_value': 0,
                    'success': result
                }
                self.db.store_automation_event(event_data)
                
                return {
                    'success': result,
                    'device': device,
                    'state': state,
                    'timestamp': get_timestamp()
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'timestamp': get_timestamp()
                }
        
        # Test device control
        response = control_device('fan', True)
        
        assert response['success'] is True
        assert response['device'] == 'fan'
        assert response['state'] is True
        
        # Verify device state
        device_state = self.automation.get_device_state('fan')
        assert device_state is True
    
    def test_historical_data_api_integration(self):
        """Test historical data API integration"""
        # Store some historical data
        for i in range(5):
            sensor_data = {
                'temperature': 25.0 + i,
                'humidity': 50.0 - i,
                'soil_moisture': 60.0 + i,
                'co2': 500.0 + i * 10,
                'timestamp': get_timestamp()
            }
            self.db.store_sensor_reading(sensor_data)
        
        def get_historical_data(hours=24):
            """Simulate /api/historical endpoint"""
            try:
                from datetime import datetime, timedelta
                
                end_time = datetime.now()
                start_time = end_time - timedelta(hours=hours)
                
                historical_data = self.db.get_historical_data(
                    start_time=start_time.isoformat(),
                    end_time=end_time.isoformat()
                )
                
                return {
                    'success': True,
                    'data': historical_data,
                    'count': len(historical_data),
                    'timestamp': get_timestamp()
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'timestamp': get_timestamp()
                }
        
        # Test historical data endpoint
        response = get_historical_data()
        
        assert response['success'] is True
        assert 'data' in response
        assert response['count'] >= 0
    
    def test_status_api_integration(self):
        """Test system status API integration"""
        def get_system_status():
            """Simulate /api/status endpoint"""
            try:
                # Get database stats
                db_stats = self.db.get_database_stats()
                
                # Get device states
                device_states = self.automation.get_all_device_states()
                
                # Get recent sensor reading
                recent_readings = self.db.get_sensor_readings(limit=1)
                
                return {
                    'success': True,
                    'database': db_stats,
                    'devices': device_states,
                    'last_reading': recent_readings[0] if recent_readings else None,
                    'timestamp': get_timestamp()
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'timestamp': get_timestamp()
                }
        
        # Store some data first
        sensor_data = {
            'temperature': 25.0,
            'humidity': 50.0,
            'soil_moisture': 60.0,
            'co2': 500.0,
            'timestamp': get_timestamp()
        }
        self.db.store_sensor_reading(sensor_data)
        
        # Test status endpoint
        response = get_system_status()
        
        assert response['success'] is True
        assert 'database' in response
        assert 'devices' in response
        assert 'last_reading' in response
        assert response['database']['sensor_readings'] >= 1

if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])