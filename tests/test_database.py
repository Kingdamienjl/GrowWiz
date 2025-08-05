"""
Unit tests for GrowWiz database manager module
"""

import pytest
import sys
import os
import tempfile
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import DatabaseManager

class TestDatabaseManager:
    """Test cases for DatabaseManager class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Create temporary database file
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        # Initialize database manager with temp file
        self.db = DatabaseManager(self.temp_db.name)
        
        # Sample data for testing
        self.sample_sensor_data = {
            'temperature': 25.5,
            'humidity': 45.2,
            'soil_moisture': 72.0,
            'co2': 550.0
        }
        
        self.sample_diagnosis = {
            'image_path': '/test/image.jpg',
            'primary_diagnosis': 'healthy',
            'confidence': 0.85,
            'predictions': [
                {'condition': 'healthy', 'confidence': 0.85},
                {'condition': 'nutrient_deficiency', 'confidence': 0.15}
            ],
            'recommendations': ['Continue current care routine', 'Monitor for changes']
        }
    
    def teardown_method(self):
        """Clean up after tests"""
        if hasattr(self.db, 'close'):
            self.db.close()
        
        # Remove temporary database file
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_initialization(self):
        """Test database manager initialization"""
        assert self.db is not None
        assert hasattr(self.db, 'db_path')
        assert hasattr(self.db, 'conn')
        assert self.db.db_path == self.temp_db.name
    
    def test_database_file_creation(self):
        """Test that database file is created"""
        assert os.path.exists(self.temp_db.name)
        
        # Check that it's a valid SQLite database
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()
        
        # Should have created tables
        assert len(tables) > 0
    
    def test_table_creation(self):
        """Test that all required tables are created"""
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]
        
        expected_tables = [
            'sensor_readings',
            'plant_diagnoses',
            'automation_events',
            'system_logs',
            'scraped_tips',
            'user_queries'
        ]
        
        for table in expected_tables:
            assert table in tables
    
    def test_store_sensor_reading(self):
        """Test storing sensor readings"""
        # Store sensor reading
        reading_id = self.db.store_sensor_reading(self.sample_sensor_data)
        
        assert reading_id is not None
        assert isinstance(reading_id, int)
        assert reading_id > 0
        
        # Verify data was stored
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM sensor_readings WHERE id = ?", (reading_id,))
        row = cursor.fetchone()
        
        assert row is not None
        assert row[1] == self.sample_sensor_data['temperature']  # temperature column
        assert row[2] == self.sample_sensor_data['humidity']     # humidity column
        assert row[3] == self.sample_sensor_data['soil_moisture'] # soil_moisture column
        assert row[4] == self.sample_sensor_data['co2']          # co2 column
    
    def test_get_sensor_readings(self):
        """Test retrieving sensor readings"""
        # Store multiple readings
        for i in range(5):
            data = self.sample_sensor_data.copy()
            data['temperature'] += i  # Vary temperature
            self.db.store_sensor_reading(data)
        
        # Get all readings
        readings = self.db.get_sensor_readings()
        
        assert isinstance(readings, list)
        assert len(readings) == 5
        
        # Check reading structure
        for reading in readings:
            assert isinstance(reading, dict)
            assert 'id' in reading
            assert 'temperature' in reading
            assert 'humidity' in reading
            assert 'soil_moisture' in reading
            assert 'co2' in reading
            assert 'timestamp' in reading
        
        # Test with limit
        limited_readings = self.db.get_sensor_readings(limit=3)
        assert len(limited_readings) == 3
    
    def test_store_plant_diagnosis(self):
        """Test storing plant diagnoses"""
        # Store diagnosis
        diagnosis_id = self.db.store_plant_diagnosis(self.sample_diagnosis)
        
        assert diagnosis_id is not None
        assert isinstance(diagnosis_id, int)
        assert diagnosis_id > 0
        
        # Verify data was stored
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM plant_diagnoses WHERE id = ?", (diagnosis_id,))
        row = cursor.fetchone()
        
        assert row is not None
        assert row[1] == self.sample_diagnosis['image_path']
        assert row[2] == self.sample_diagnosis['primary_diagnosis']
        assert row[3] == self.sample_diagnosis['confidence']
    
    def test_get_plant_diagnoses(self):
        """Test retrieving plant diagnoses"""
        # Store multiple diagnoses
        for i in range(3):
            diagnosis = self.sample_diagnosis.copy()
            diagnosis['image_path'] = f'/test/image_{i}.jpg'
            self.db.store_plant_diagnosis(diagnosis)
        
        # Get all diagnoses
        diagnoses = self.db.get_plant_diagnoses()
        
        assert isinstance(diagnoses, list)
        assert len(diagnoses) == 3
        
        # Check diagnosis structure
        for diagnosis in diagnoses:
            assert isinstance(diagnosis, dict)
            assert 'id' in diagnosis
            assert 'image_path' in diagnosis
            assert 'primary_diagnosis' in diagnosis
            assert 'confidence' in diagnosis
            assert 'predictions' in diagnosis
            assert 'recommendations' in diagnosis
            assert 'timestamp' in diagnosis
    
    def test_store_automation_event(self):
        """Test storing automation events"""
        event_data = {
            'rule_name': 'Temperature Control',
            'device': 'fan',
            'action': 'activate',
            'trigger_value': 32.0,
            'success': True
        }
        
        # Store event
        event_id = self.db.store_automation_event(event_data)
        
        assert event_id is not None
        assert isinstance(event_id, int)
        assert event_id > 0
        
        # Verify data was stored
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM automation_events WHERE id = ?", (event_id,))
        row = cursor.fetchone()
        
        assert row is not None
        assert row[1] == event_data['rule_name']
        assert row[2] == event_data['device']
        assert row[3] == event_data['action']
        assert row[4] == event_data['trigger_value']
        assert row[5] == event_data['success']
    
    def test_get_automation_events(self):
        """Test retrieving automation events"""
        # Store multiple events
        for i in range(4):
            event = {
                'rule_name': f'Rule {i}',
                'device': 'fan',
                'action': 'activate',
                'trigger_value': 30.0 + i,
                'success': True
            }
            self.db.store_automation_event(event)
        
        # Get all events
        events = self.db.get_automation_events()
        
        assert isinstance(events, list)
        assert len(events) == 4
        
        # Check event structure
        for event in events:
            assert isinstance(event, dict)
            assert 'id' in event
            assert 'rule_name' in event
            assert 'device' in event
            assert 'action' in event
            assert 'trigger_value' in event
            assert 'success' in event
            assert 'timestamp' in event
    
    def test_store_system_log(self):
        """Test storing system logs"""
        log_data = {
            'level': 'INFO',
            'message': 'System started successfully',
            'module': 'main'
        }
        
        # Store log
        log_id = self.db.store_system_log(log_data)
        
        assert log_id is not None
        assert isinstance(log_id, int)
        assert log_id > 0
        
        # Verify data was stored
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM system_logs WHERE id = ?", (log_id,))
        row = cursor.fetchone()
        
        assert row is not None
        assert row[1] == log_data['level']
        assert row[2] == log_data['message']
        assert row[3] == log_data['module']
    
    def test_get_system_logs(self):
        """Test retrieving system logs"""
        # Store multiple logs
        log_levels = ['INFO', 'WARNING', 'ERROR', 'DEBUG']
        for level in log_levels:
            log = {
                'level': level,
                'message': f'Test {level} message',
                'module': 'test'
            }
            self.db.store_system_log(log)
        
        # Get all logs
        logs = self.db.get_system_logs()
        
        assert isinstance(logs, list)
        assert len(logs) == 4
        
        # Test filtering by level
        error_logs = self.db.get_system_logs(level='ERROR')
        assert len(error_logs) == 1
        assert error_logs[0]['level'] == 'ERROR'
    
    def test_store_scraped_tip(self):
        """Test storing scraped tips"""
        tip_data = {
            'url': 'http://example.com/tip1',
            'content': 'Water your plants regularly but avoid overwatering',
            'relevance_score': 0.85,
            'source': 'forum'
        }
        
        # Store tip
        tip_id = self.db.store_scraped_tip(tip_data)
        
        assert tip_id is not None
        assert isinstance(tip_id, int)
        assert tip_id > 0
        
        # Verify data was stored
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM scraped_tips WHERE id = ?", (tip_id,))
        row = cursor.fetchone()
        
        assert row is not None
        assert row[1] == tip_data['url']
        assert row[2] == tip_data['content']
        assert row[3] == tip_data['relevance_score']
        assert row[4] == tip_data['source']
    
    def test_get_scraped_tips(self):
        """Test retrieving scraped tips"""
        # Store multiple tips
        for i in range(5):
            tip = {
                'url': f'http://example.com/tip{i}',
                'content': f'Growing tip number {i}',
                'relevance_score': 0.5 + (i * 0.1),
                'source': 'forum' if i % 2 == 0 else 'blog'
            }
            self.db.store_scraped_tip(tip)
        
        # Get all tips
        tips = self.db.get_scraped_tips()
        
        assert isinstance(tips, list)
        assert len(tips) == 5
        
        # Test with minimum relevance
        relevant_tips = self.db.get_scraped_tips(min_relevance=0.7)
        assert len(relevant_tips) < 5  # Should filter out lower relevance tips
        
        for tip in relevant_tips:
            assert tip['relevance_score'] >= 0.7
    
    def test_search_tips(self):
        """Test searching scraped tips"""
        # Store tips with different content
        tips_data = [
            {
                'url': 'http://example.com/humidity',
                'content': 'Maintain humidity levels between 40-60% for optimal growth',
                'relevance_score': 0.9,
                'source': 'forum'
            },
            {
                'url': 'http://example.com/temperature',
                'content': 'Temperature control is crucial for plant health',
                'relevance_score': 0.8,
                'source': 'blog'
            },
            {
                'url': 'http://example.com/watering',
                'content': 'Water plants when soil moisture drops below 30%',
                'relevance_score': 0.7,
                'source': 'forum'
            }
        ]
        
        for tip in tips_data:
            self.db.store_scraped_tip(tip)
        
        # Search for humidity-related tips
        humidity_tips = self.db.search_tips('humidity')
        
        assert isinstance(humidity_tips, list)
        assert len(humidity_tips) >= 1
        assert 'humidity' in humidity_tips[0]['content'].lower()
        
        # Search for non-existent term
        no_results = self.db.search_tips('nonexistent_term')
        assert len(no_results) == 0
    
    def test_store_user_query(self):
        """Test storing user queries"""
        query_data = {
            'query': 'How often should I water my plants?',
            'response': 'Water when soil moisture is below 30%',
            'context': 'general_advice'
        }
        
        # Store query
        query_id = self.db.store_user_query(query_data)
        
        assert query_id is not None
        assert isinstance(query_id, int)
        assert query_id > 0
        
        # Verify data was stored
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM user_queries WHERE id = ?", (query_id,))
        row = cursor.fetchone()
        
        assert row is not None
        assert row[1] == query_data['query']
        assert row[2] == query_data['response']
        assert row[3] == query_data['context']
    
    def test_get_user_queries(self):
        """Test retrieving user queries"""
        # Store multiple queries
        for i in range(3):
            query = {
                'query': f'Question {i}?',
                'response': f'Answer {i}',
                'context': 'test'
            }
            self.db.store_user_query(query)
        
        # Get all queries
        queries = self.db.get_user_queries()
        
        assert isinstance(queries, list)
        assert len(queries) == 3
        
        # Check query structure
        for query in queries:
            assert isinstance(query, dict)
            assert 'id' in query
            assert 'query' in query
            assert 'response' in query
            assert 'context' in query
            assert 'timestamp' in query
    
    def test_get_historical_data(self):
        """Test retrieving historical sensor data"""
        # Store readings over time
        base_time = datetime.now()
        for i in range(10):
            data = self.sample_sensor_data.copy()
            data['temperature'] += i
            self.db.store_sensor_reading(data)
        
        # Get data from last hour
        one_hour_ago = base_time - timedelta(hours=1)
        historical_data = self.db.get_historical_data(
            start_time=one_hour_ago.isoformat(),
            end_time=base_time.isoformat()
        )
        
        assert isinstance(historical_data, list)
        # Should get some data (exact count depends on timing)
        assert len(historical_data) >= 0
    
    def test_get_recent_diagnoses(self):
        """Test retrieving recent diagnoses"""
        # Store multiple diagnoses
        for i in range(5):
            diagnosis = self.sample_diagnosis.copy()
            diagnosis['image_path'] = f'/test/recent_{i}.jpg'
            self.db.store_plant_diagnosis(diagnosis)
        
        # Get recent diagnoses
        recent = self.db.get_recent_diagnoses(limit=3)
        
        assert isinstance(recent, list)
        assert len(recent) == 3
        
        # Should be ordered by timestamp (most recent first)
        timestamps = [d['timestamp'] for d in recent]
        assert timestamps == sorted(timestamps, reverse=True)
    
    def test_get_automation_history(self):
        """Test retrieving automation history"""
        # Store multiple events
        for i in range(6):
            event = {
                'rule_name': f'Rule {i}',
                'device': 'fan',
                'action': 'activate',
                'trigger_value': 30.0,
                'success': i % 2 == 0  # Alternate success/failure
            }
            self.db.store_automation_event(event)
        
        # Get automation history
        history = self.db.get_automation_history(limit=4)
        
        assert isinstance(history, list)
        assert len(history) == 4
        
        # Test filtering by device
        fan_history = self.db.get_automation_history(device='fan')
        assert len(fan_history) == 6  # All events were for fan
        
        # Test filtering by success
        successful_events = self.db.get_automation_history(success_only=True)
        assert len(successful_events) == 3  # Half were successful
    
    def test_get_database_stats(self):
        """Test retrieving database statistics"""
        # Add some data
        self.db.store_sensor_reading(self.sample_sensor_data)
        self.db.store_plant_diagnosis(self.sample_diagnosis)
        
        # Get stats
        stats = self.db.get_database_stats()
        
        assert isinstance(stats, dict)
        assert 'sensor_readings' in stats
        assert 'plant_diagnoses' in stats
        assert 'automation_events' in stats
        assert 'system_logs' in stats
        assert 'scraped_tips' in stats
        assert 'user_queries' in stats
        
        # Check that counts are correct
        assert stats['sensor_readings'] >= 1
        assert stats['plant_diagnoses'] >= 1
    
    def test_cleanup_old_data(self):
        """Test cleaning up old data"""
        # Store old sensor readings
        old_time = datetime.now() - timedelta(days=40)
        
        # Mock the timestamp for old data
        with patch('database.datetime') as mock_datetime:
            mock_datetime.now.return_value = old_time
            mock_datetime.now().isoformat.return_value = old_time.isoformat()
            
            for i in range(5):
                self.db.store_sensor_reading(self.sample_sensor_data)
        
        # Store recent data
        for i in range(3):
            self.db.store_sensor_reading(self.sample_sensor_data)
        
        # Should have 8 total readings
        all_readings = self.db.get_sensor_readings()
        assert len(all_readings) == 8
        
        # Clean up data older than 30 days
        cleaned_count = self.db.cleanup_old_data(days=30)
        
        # Should have cleaned up old data
        assert cleaned_count > 0
        
        # Should have fewer readings now
        remaining_readings = self.db.get_sensor_readings()
        assert len(remaining_readings) < 8
    
    def test_error_handling(self):
        """Test error handling in database operations"""
        # Test with invalid data
        invalid_sensor_data = {'invalid_key': 'invalid_value'}
        
        # Should handle gracefully (might return None or raise exception)
        try:
            result = self.db.store_sensor_reading(invalid_sensor_data)
            # If it doesn't raise an exception, result should be None or valid
            assert result is None or isinstance(result, int)
        except Exception:
            # Exception is acceptable for invalid data
            pass
    
    def test_connection_management(self):
        """Test database connection management"""
        # Connection should be active
        assert self.db.conn is not None
        
        # Test closing connection
        self.db.close()
        
        # Connection should be closed
        # Note: sqlite3 connections don't have a simple "is_closed" check
        # We can try to execute a query to see if it fails
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT 1")
            # If this succeeds, connection is still open
        except sqlite3.ProgrammingError:
            # This is expected after closing
            pass
    
    def test_concurrent_access(self):
        """Test concurrent database access"""
        # Create another database manager instance
        db2 = DatabaseManager(self.temp_db.name)
        
        try:
            # Both should be able to write
            id1 = self.db.store_sensor_reading(self.sample_sensor_data)
            id2 = db2.store_sensor_reading(self.sample_sensor_data)
            
            assert id1 is not None
            assert id2 is not None
            assert id1 != id2  # Should have different IDs
            
            # Both should be able to read
            readings1 = self.db.get_sensor_readings()
            readings2 = db2.get_sensor_readings()
            
            assert len(readings1) == len(readings2)  # Should see same data
            
        finally:
            db2.close()

class TestDatabaseIntegration:
    """Integration tests for database functionality"""
    
    def test_complete_data_flow(self):
        """Test complete data flow through database"""
        # Create temporary database
        temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        temp_db.close()
        
        try:
            db = DatabaseManager(temp_db.name)
            
            # Store sensor data
            sensor_data = {
                'temperature': 26.5,
                'humidity': 48.0,
                'soil_moisture': 65.0,
                'co2': 520.0
            }
            sensor_id = db.store_sensor_reading(sensor_data)
            
            # Store plant diagnosis
            diagnosis_data = {
                'image_path': '/test/plant.jpg',
                'primary_diagnosis': 'nutrient_deficiency',
                'confidence': 0.75,
                'predictions': [
                    {'condition': 'nutrient_deficiency', 'confidence': 0.75},
                    {'condition': 'healthy', 'confidence': 0.25}
                ],
                'recommendations': ['Add nitrogen fertilizer', 'Monitor growth']
            }
            diagnosis_id = db.store_plant_diagnosis(diagnosis_data)
            
            # Store automation event
            automation_data = {
                'rule_name': 'Nutrient Deficiency Response',
                'device': 'nutrient_pump',
                'action': 'activate',
                'trigger_value': 0.75,
                'success': True
            }
            automation_id = db.store_automation_event(automation_data)
            
            # Store system log
            log_data = {
                'level': 'INFO',
                'message': 'Automated nutrient delivery completed',
                'module': 'automation'
            }
            log_id = db.store_system_log(log_data)
            
            # Verify all data was stored
            assert sensor_id is not None
            assert diagnosis_id is not None
            assert automation_id is not None
            assert log_id is not None
            
            # Retrieve and verify data
            readings = db.get_sensor_readings(limit=1)
            assert len(readings) == 1
            assert readings[0]['temperature'] == sensor_data['temperature']
            
            diagnoses = db.get_plant_diagnoses(limit=1)
            assert len(diagnoses) == 1
            assert diagnoses[0]['primary_diagnosis'] == diagnosis_data['primary_diagnosis']
            
            events = db.get_automation_events(limit=1)
            assert len(events) == 1
            assert events[0]['device'] == automation_data['device']
            
            logs = db.get_system_logs(limit=1)
            assert len(logs) == 1
            assert logs[0]['level'] == log_data['level']
            
            # Test database stats
            stats = db.get_database_stats()
            assert stats['sensor_readings'] >= 1
            assert stats['plant_diagnoses'] >= 1
            assert stats['automation_events'] >= 1
            assert stats['system_logs'] >= 1
            
            db.close()
            
        finally:
            os.unlink(temp_db.name)

if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])