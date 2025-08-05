#!/usr/bin/env python3
"""
GrowWiz Database Manager
Handles data storage and retrieval for sensor readings and system logs
"""

import os
import sqlite3
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from loguru import logger

class DatabaseManager:
    """Manages SQLite database for GrowWiz data storage"""
    
    def __init__(self):
        self.db_path = os.getenv("DATABASE_PATH", "./data/growwiz.db")
        self.connection = None
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        logger.info(f"DatabaseManager initialized with database: {self.db_path}")
    
    async def initialize(self):
        """Initialize database connection and create tables"""
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row  # Enable dict-like access
            
            await self._create_tables()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def _create_tables(self):
        """Create necessary database tables"""
        cursor = self.connection.cursor()
        
        try:
            # Sensor readings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sensor_readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    temperature REAL,
                    humidity REAL,
                    soil_moisture REAL,
                    co2 REAL,
                    simulation_mode BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Plant diagnoses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS plant_diagnoses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    image_path TEXT,
                    primary_diagnosis TEXT,
                    confidence REAL,
                    predictions TEXT,  -- JSON string
                    features TEXT,     -- JSON string
                    recommendations TEXT,  -- JSON string
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Automation events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS automation_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    rule_name TEXT NOT NULL,
                    device_name TEXT,
                    action TEXT,
                    sensor_data TEXT,  -- JSON string
                    success BOOLEAN DEFAULT 1,
                    error_message TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # System logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    level TEXT NOT NULL,
                    module TEXT,
                    message TEXT NOT NULL,
                    details TEXT,  -- JSON string for additional data
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Scraped tips table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scraped_tips (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    source TEXT NOT NULL,
                    type TEXT,
                    content TEXT NOT NULL,
                    keywords TEXT,  -- JSON string
                    relevance_score REAL DEFAULT 0.0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # User queries table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_queries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    query TEXT NOT NULL,
                    response TEXT,
                    sensor_context TEXT,  -- JSON string
                    satisfaction_rating INTEGER,  -- 1-5 scale
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sensor_timestamp ON sensor_readings(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_diagnosis_timestamp ON plant_diagnoses(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_automation_timestamp ON automation_events(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON system_logs(timestamp)")
            
            self.connection.commit()
            logger.info("Database tables created successfully")
            
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    async def store_sensor_data(self, sensor_data: Dict[str, Any]) -> int:
        """Store sensor reading in database"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                INSERT INTO sensor_readings 
                (timestamp, temperature, humidity, soil_moisture, co2, simulation_mode)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                sensor_data.get("timestamp", time.time()),
                sensor_data.get("temperature"),
                sensor_data.get("humidity"),
                sensor_data.get("soil_moisture"),
                sensor_data.get("co2"),
                sensor_data.get("simulation_mode", False)
            ))
            
            self.connection.commit()
            reading_id = cursor.lastrowid
            
            logger.debug(f"Stored sensor reading with ID: {reading_id}")
            return reading_id
            
        except Exception as e:
            logger.error(f"Error storing sensor data: {e}")
            raise
    
    async def store_plant_diagnosis(self, diagnosis: Dict[str, Any]) -> int:
        """Store plant diagnosis result in database"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                INSERT INTO plant_diagnoses 
                (timestamp, image_path, primary_diagnosis, confidence, predictions, features, recommendations)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                diagnosis.get("timestamp", time.time()),
                diagnosis.get("image_path"),
                diagnosis.get("primary_diagnosis"),
                diagnosis.get("confidence"),
                json.dumps(diagnosis.get("predictions", [])),
                json.dumps(diagnosis.get("features", {})),
                json.dumps(diagnosis.get("recommendations", []))
            ))
            
            self.connection.commit()
            diagnosis_id = cursor.lastrowid
            
            logger.info(f"Stored plant diagnosis with ID: {diagnosis_id}")
            return diagnosis_id
            
        except Exception as e:
            logger.error(f"Error storing plant diagnosis: {e}")
            raise
    
    async def store_automation_event(self, event: Dict[str, Any]) -> int:
        """Store automation event in database"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                INSERT INTO automation_events 
                (timestamp, rule_name, device_name, action, sensor_data, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                event.get("timestamp", time.time()),
                event.get("rule_name"),
                event.get("device_name"),
                event.get("action"),
                json.dumps(event.get("sensor_data", {})),
                event.get("success", True),
                event.get("error_message")
            ))
            
            self.connection.commit()
            event_id = cursor.lastrowid
            
            logger.debug(f"Stored automation event with ID: {event_id}")
            return event_id
            
        except Exception as e:
            logger.error(f"Error storing automation event: {e}")
            raise
    
    async def store_scraped_tip(self, tip: Dict[str, Any]) -> int:
        """Store scraped growing tip in database"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                INSERT INTO scraped_tips 
                (timestamp, source, type, content, keywords, relevance_score)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                tip.get("timestamp", time.time()),
                tip.get("source"),
                tip.get("type"),
                tip.get("content"),
                json.dumps(tip.get("keywords", [])),
                tip.get("relevance_score", 0.0)
            ))
            
            self.connection.commit()
            tip_id = cursor.lastrowid
            
            logger.debug(f"Stored scraped tip with ID: {tip_id}")
            return tip_id
            
        except Exception as e:
            logger.error(f"Error storing scraped tip: {e}")
            raise
    
    async def store_user_query(self, query_data: Dict[str, Any]) -> int:
        """Store user query and response in database"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                INSERT INTO user_queries 
                (timestamp, query, response, sensor_context, satisfaction_rating)
                VALUES (?, ?, ?, ?, ?)
            """, (
                query_data.get("timestamp", time.time()),
                query_data.get("query"),
                query_data.get("response"),
                json.dumps(query_data.get("sensor_context", {})),
                query_data.get("satisfaction_rating")
            ))
            
            self.connection.commit()
            query_id = cursor.lastrowid
            
            logger.debug(f"Stored user query with ID: {query_id}")
            return query_id
            
        except Exception as e:
            logger.error(f"Error storing user query: {e}")
            raise
    
    async def get_sensor_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get sensor readings from the last N hours"""
        try:
            cursor = self.connection.cursor()
            
            # Calculate timestamp for N hours ago
            cutoff_time = time.time() - (hours * 3600)
            
            cursor.execute("""
                SELECT * FROM sensor_readings 
                WHERE timestamp > ? 
                ORDER BY timestamp DESC
            """, (cutoff_time,))
            
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            history = []
            for row in rows:
                history.append({
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "temperature": row["temperature"],
                    "humidity": row["humidity"],
                    "soil_moisture": row["soil_moisture"],
                    "co2": row["co2"],
                    "simulation_mode": bool(row["simulation_mode"]),
                    "created_at": row["created_at"]
                })
            
            logger.debug(f"Retrieved {len(history)} sensor readings from last {hours} hours")
            return history
            
        except Exception as e:
            logger.error(f"Error retrieving sensor history: {e}")
            return []
    
    async def get_recent_diagnoses(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent plant diagnoses"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute("""
                SELECT * FROM plant_diagnoses 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            
            diagnoses = []
            for row in rows:
                diagnoses.append({
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "image_path": row["image_path"],
                    "primary_diagnosis": row["primary_diagnosis"],
                    "confidence": row["confidence"],
                    "predictions": json.loads(row["predictions"] or "[]"),
                    "features": json.loads(row["features"] or "{}"),
                    "recommendations": json.loads(row["recommendations"] or "[]"),
                    "created_at": row["created_at"]
                })
            
            logger.debug(f"Retrieved {len(diagnoses)} recent diagnoses")
            return diagnoses
            
        except Exception as e:
            logger.error(f"Error retrieving recent diagnoses: {e}")
            return []
    
    async def get_automation_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get automation events from the last N hours"""
        try:
            cursor = self.connection.cursor()
            
            cutoff_time = time.time() - (hours * 3600)
            
            cursor.execute("""
                SELECT * FROM automation_events 
                WHERE timestamp > ? 
                ORDER BY timestamp DESC
            """, (cutoff_time,))
            
            rows = cursor.fetchall()
            
            events = []
            for row in rows:
                events.append({
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "rule_name": row["rule_name"],
                    "device_name": row["device_name"],
                    "action": row["action"],
                    "sensor_data": json.loads(row["sensor_data"] or "{}"),
                    "success": bool(row["success"]),
                    "error_message": row["error_message"],
                    "created_at": row["created_at"]
                })
            
            logger.debug(f"Retrieved {len(events)} automation events from last {hours} hours")
            return events
            
        except Exception as e:
            logger.error(f"Error retrieving automation history: {e}")
            return []
    
    async def search_tips(self, keywords: List[str], limit: int = 20) -> List[Dict[str, Any]]:
        """Search scraped tips by keywords"""
        try:
            cursor = self.connection.cursor()
            
            # Build search query
            search_terms = " OR ".join([f"content LIKE '%{keyword}%'" for keyword in keywords])
            
            cursor.execute(f"""
                SELECT * FROM scraped_tips 
                WHERE {search_terms}
                ORDER BY relevance_score DESC, timestamp DESC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            
            tips = []
            for row in rows:
                tips.append({
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "source": row["source"],
                    "type": row["type"],
                    "content": row["content"],
                    "keywords": json.loads(row["keywords"] or "[]"),
                    "relevance_score": row["relevance_score"],
                    "created_at": row["created_at"]
                })
            
            logger.debug(f"Found {len(tips)} tips matching keywords: {keywords}")
            return tips
            
        except Exception as e:
            logger.error(f"Error searching tips: {e}")
            return []
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics and summary information"""
        try:
            cursor = self.connection.cursor()
            
            stats = {}
            
            # Count records in each table
            tables = [
                "sensor_readings", "plant_diagnoses", "automation_events",
                "system_logs", "scraped_tips", "user_queries"
            ]
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                stats[f"{table}_count"] = count
            
            # Get latest sensor reading
            cursor.execute("""
                SELECT * FROM sensor_readings 
                ORDER BY timestamp DESC 
                LIMIT 1
            """)
            latest_reading = cursor.fetchone()
            if latest_reading:
                stats["latest_sensor_reading"] = {
                    "timestamp": latest_reading["timestamp"],
                    "temperature": latest_reading["temperature"],
                    "humidity": latest_reading["humidity"],
                    "soil_moisture": latest_reading["soil_moisture"],
                    "co2": latest_reading["co2"]
                }
            
            # Get database file size
            if os.path.exists(self.db_path):
                stats["database_size_mb"] = round(os.path.getsize(self.db_path) / (1024 * 1024), 2)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting database statistics: {e}")
            return {}
    
    def get_timestamp(self) -> float:
        """Get current timestamp"""
        return time.time()
    
    def format_timestamp(self, timestamp: float) -> str:
        """Format timestamp as human-readable string"""
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    
    async def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old data to prevent database from growing too large"""
        try:
            cursor = self.connection.cursor()
            
            # Calculate cutoff timestamp
            cutoff_time = time.time() - (days_to_keep * 24 * 3600)
            
            # Clean up old sensor readings (keep more recent ones)
            cursor.execute("DELETE FROM sensor_readings WHERE timestamp < ?", (cutoff_time,))
            sensor_deleted = cursor.rowcount
            
            # Clean up old automation events
            cursor.execute("DELETE FROM automation_events WHERE timestamp < ?", (cutoff_time,))
            automation_deleted = cursor.rowcount
            
            # Clean up old system logs
            cursor.execute("DELETE FROM system_logs WHERE timestamp < ?", (cutoff_time,))
            logs_deleted = cursor.rowcount
            
            self.connection.commit()
            
            logger.info(f"Cleaned up old data: {sensor_deleted} sensor readings, "
                       f"{automation_deleted} automation events, {logs_deleted} log entries")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")

# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_database():
        db = DatabaseManager()
        
        try:
            await db.initialize()
            
            # Test storing sensor data
            sensor_data = {
                "temperature": 24.5,
                "humidity": 55.0,
                "soil_moisture": 65.0,
                "co2": 450.0,
                "simulation_mode": True
            }
            
            reading_id = await db.store_sensor_data(sensor_data)
            print(f"Stored sensor reading with ID: {reading_id}")
            
            # Test retrieving history
            history = await db.get_sensor_history(1)  # Last 1 hour
            print(f"Retrieved {len(history)} historical readings")
            
            # Test statistics
            stats = await db.get_statistics()
            print(f"Database statistics: {json.dumps(stats, indent=2)}")
            
        finally:
            db.close()
    
    # Run the test
    asyncio.run(test_database())