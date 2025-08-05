#!/usr/bin/env python3
"""
GrowWiz Command Line Interface
Provides CLI access to GrowWiz functionality
"""

import os
import sys
import json
import asyncio
import argparse
from typing import Dict, Any
from loguru import logger

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sensors import SensorManager
from plant_classifier import PlantClassifier
from scraper import GrowTipScraper
from automation import AutomationEngine
from database import DatabaseManager

class GrowWizCLI:
    """Command line interface for GrowWiz operations"""
    
    def __init__(self):
        self.sensor_manager = SensorManager()
        self.plant_classifier = PlantClassifier()
        self.scraper = GrowTipScraper()
        self.automation_engine = AutomationEngine()
        self.db_manager = DatabaseManager()
        
        logger.info("GrowWiz CLI initialized")
    
    async def initialize(self):
        """Initialize async components"""
        await self.db_manager.initialize()
    
    def monitor_sensors(self, continuous: bool = False, interval: int = 60):
        """Monitor sensor readings"""
        try:
            if continuous:
                print("Starting continuous sensor monitoring (Ctrl+C to stop)...")
                while True:
                    readings = self.sensor_manager.read_all_sensors()
                    self._print_sensor_data(readings)
                    
                    if not continuous:
                        break
                    
                    import time
                    time.sleep(interval)
            else:
                readings = self.sensor_manager.read_all_sensors()
                self._print_sensor_data(readings)
                
        except KeyboardInterrupt:
            print("\\nStopping sensor monitoring...")
        except Exception as e:
            logger.error(f"Error monitoring sensors: {e}")
            print(f"Error: {e}")
    
    def _print_sensor_data(self, data: Dict[str, Any]):
        """Pretty print sensor data"""
        print(f"\\n{'='*50}")
        print(f"Sensor Readings - {self.db_manager.format_timestamp(data.get('timestamp', 0))}")
        print(f"{'='*50}")
        print(f"🌡️  Temperature: {data.get('temperature', 'N/A')}°C")
        print(f"💧 Humidity: {data.get('humidity', 'N/A')}%")
        print(f"🌱 Soil Moisture: {data.get('soil_moisture', 'N/A')}%")
        print(f"🌬️  CO2: {data.get('co2', 'N/A')} ppm")
        
        if data.get('simulation_mode'):
            print("⚠️  Running in simulation mode")
        
        print(f"{'='*50}")
    
    def diagnose_plant(self, image_path: str):
        """Diagnose plant health from image"""
        try:
            if not os.path.exists(image_path):
                print(f"Error: Image file not found: {image_path}")
                return
            
            print(f"Analyzing plant image: {image_path}")
            print("This may take a moment...")
            
            result = self.plant_classifier.classify_image(image_path)
            
            self._print_diagnosis_result(result)
            
        except Exception as e:
            logger.error(f"Error diagnosing plant: {e}")
            print(f"Error: {e}")
    
    def _print_diagnosis_result(self, result: Dict[str, Any]):
        """Pretty print diagnosis result"""
        print(f"\\n{'='*60}")
        print(f"Plant Diagnosis Results")
        print(f"{'='*60}")
        
        if result.get('error'):
            print(f"❌ Error: {result.get('error_message', 'Unknown error')}")
            return
        
        print(f"📸 Image: {result.get('image_path', 'N/A')}")
        print(f"🔍 Primary Diagnosis: {result.get('primary_diagnosis', 'Unknown')}")
        print(f"📊 Confidence: {result.get('confidence', 0):.1%}")
        
        if result.get('simulation_mode'):
            print("⚠️  Running in simulation mode")
        
        # Show top predictions
        predictions = result.get('predictions', [])
        if predictions:
            print(f"\\n🎯 Top Predictions:")
            for i, pred in enumerate(predictions[:3], 1):
                print(f"  {i}. {pred.get('condition', 'Unknown')} ({pred.get('confidence', 0):.1%})")
        
        # Show recommendations
        recommendations = result.get('recommendations', [])
        if recommendations:
            print(f"\\n💡 Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        
        # Show features
        features = result.get('features', {})
        if features:
            print(f"\\n📈 Image Analysis:")
            print(f"  • Green area: {features.get('green_percentage', 0):.1f}%")
            print(f"  • Problem areas: {features.get('problem_area_percentage', 0):.1f}%")
            print(f"  • Brightness: {features.get('brightness', 0):.1f}")
        
        print(f"{'='*60}")
    
    async def get_advice(self, question: str):
        """Get AI-powered growing advice"""
        try:
            print(f"Getting advice for: '{question}'")
            print("Searching knowledge base...")
            
            # Get current sensor context
            current_sensors = self.sensor_manager.read_all_sensors()
            
            # Search for relevant tips
            relevant_tips = await self.scraper.get_relevant_tips(question)
            
            self._print_advice_result(question, current_sensors, relevant_tips)
            
        except Exception as e:
            logger.error(f"Error getting advice: {e}")
            print(f"Error: {e}")
    
    def _print_advice_result(self, question: str, sensors: Dict[str, Any], tips: list):
        """Pretty print advice result"""
        print(f"\\n{'='*60}")
        print(f"Growing Advice")
        print(f"{'='*60}")
        print(f"❓ Question: {question}")
        
        # Show current conditions
        print(f"\\n🌡️ Current Conditions:")
        print(f"  • Temperature: {sensors.get('temperature', 'N/A')}°C")
        print(f"  • Humidity: {sensors.get('humidity', 'N/A')}%")
        print(f"  • Soil Moisture: {sensors.get('soil_moisture', 'N/A')}%")
        print(f"  • CO2: {sensors.get('co2', 'N/A')} ppm")
        
        # Show relevant tips
        if tips:
            print(f"\\n💡 Relevant Tips ({len(tips)} found):")
            for i, tip in enumerate(tips[:5], 1):  # Show top 5
                print(f"\\n  {i}. {tip.get('content', 'No content')[:200]}...")
                print(f"     Source: {tip.get('source', 'Unknown')}")
                if tip.get('keywords'):
                    print(f"     Keywords: {', '.join(tip['keywords'][:3])}")
        else:
            print(f"\\n❌ No specific tips found for your question.")
            print(f"   Try rephrasing or check our general growing guides.")
        
        print(f"{'='*60}")
    
    def automation_status(self):
        """Show automation system status"""
        try:
            status = self.automation_engine.get_status()
            
            print(f"\\n{'='*50}")
            print(f"Automation System Status")
            print(f"{'='*50}")
            
            print(f"🤖 Mode: {'Simulation' if status['simulation_mode'] else 'Hardware'}")
            print(f"📋 Rules: {status['active_rules']}/{status['total_rules']} active")
            
            # Device states
            print(f"\\n🔌 Device States:")
            for device, state in status['device_states'].items():
                status_icon = "🟢" if state else "🔴"
                print(f"  {status_icon} {device.replace('_', ' ').title()}: {'ON' if state else 'OFF'}")
            
            # Recent rules
            rules = status.get('rules', [])
            if rules:
                print(f"\\n📜 Automation Rules:")
                for rule in rules[:5]:  # Show first 5 rules
                    status_icon = "✅" if rule['enabled'] else "❌"
                    print(f"  {status_icon} {rule['name']}: {rule['description']}")
            
            print(f"{'='*50}")
            
        except Exception as e:
            logger.error(f"Error getting automation status: {e}")
            print(f"Error: {e}")
    
    def test_automation(self):
        """Test automation with sample data"""
        try:
            print("Testing automation system with sample data...")
            
            # Test data that should trigger some rules
            test_data = {
                "temperature": 32,  # High temperature
                "humidity": 35,     # Low humidity
                "soil_moisture": 25, # Low soil moisture
                "co2": 500,
                "timestamp": self.db_manager.get_timestamp()
            }
            
            print(f"\\nTest sensor data:")
            self._print_sensor_data(test_data)
            
            # Check automation
            triggered = self.automation_engine.check_and_trigger(test_data)
            
            if triggered:
                print(f"\\n🚨 Triggered {len(triggered)} automation rules:")
                for rule in triggered:
                    print(f"  • {rule}")
            else:
                print(f"\\n✅ No automation rules triggered")
            
        except Exception as e:
            logger.error(f"Error testing automation: {e}")
            print(f"Error: {e}")
    
    async def scrape_tips(self, max_pages: int = 10):
        """Scrape growing tips from web sources"""
        try:
            print(f"Starting web scraping (max {max_pages} pages)...")
            print("This may take several minutes...")
            
            # Set max pages
            self.scraper.max_pages = max_pages
            
            tips = await self.scraper.scrape_grow_forums()
            
            print(f"\\n✅ Scraping completed!")
            print(f"📚 Collected {len(tips)} growing tips")
            
            if tips:
                print(f"\\n📝 Sample tips:")
                for i, tip in enumerate(tips[:3], 1):
                    print(f"\\n  {i}. {tip.get('content', 'No content')[:150]}...")
                    print(f"     Source: {tip.get('source', 'Unknown')}")
                    print(f"     Type: {tip.get('type', 'Unknown')}")
            
        except Exception as e:
            logger.error(f"Error scraping tips: {e}")
            print(f"Error: {e}")
    
    async def database_stats(self):
        """Show database statistics"""
        try:
            stats = await self.db_manager.get_statistics()
            
            print(f"\\n{'='*50}")
            print(f"Database Statistics")
            print(f"{'='*50}")
            
            # Record counts
            print(f"📊 Record Counts:")
            for key, value in stats.items():
                if key.endswith('_count'):
                    table_name = key.replace('_count', '').replace('_', ' ').title()
                    print(f"  • {table_name}: {value:,}")
            
            # Latest reading
            if 'latest_sensor_reading' in stats:
                reading = stats['latest_sensor_reading']
                print(f"\\n🕐 Latest Sensor Reading:")
                print(f"  • Time: {self.db_manager.format_timestamp(reading['timestamp'])}")
                print(f"  • Temperature: {reading['temperature']}°C")
                print(f"  • Humidity: {reading['humidity']}%")
            
            # Database size
            if 'database_size_mb' in stats:
                print(f"\\n💾 Database Size: {stats['database_size_mb']} MB")
            
            print(f"{'='*50}")
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            print(f"Error: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        try:
            self.sensor_manager.cleanup()
            self.automation_engine.cleanup()
            self.db_manager.close()
            if hasattr(self.scraper, 'cleanup'):
                self.scraper.cleanup()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

async def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="GrowWiz - AI-powered cultivation assistant")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Monitor command
    monitor_parser = subparsers.add_parser('monitor', help='Monitor sensor readings')
    monitor_parser.add_argument('--continuous', '-c', action='store_true', 
                               help='Continuous monitoring')
    monitor_parser.add_argument('--interval', '-i', type=int, default=60,
                               help='Monitoring interval in seconds (default: 60)')
    
    # Diagnose command
    diagnose_parser = subparsers.add_parser('diagnose', help='Diagnose plant health from image')
    diagnose_parser.add_argument('--image', '-img', required=True,
                                help='Path to plant image')
    
    # Advice command
    advice_parser = subparsers.add_parser('advice', help='Get growing advice')
    advice_parser.add_argument('question', help='Your growing question')
    
    # Automation commands
    subparsers.add_parser('automation', help='Show automation status')
    subparsers.add_parser('test-automation', help='Test automation system')
    
    # Scraping command
    scrape_parser = subparsers.add_parser('scrape', help='Scrape growing tips from web')
    scrape_parser.add_argument('--max-pages', '-m', type=int, default=10,
                              help='Maximum pages to scrape (default: 10)')
    
    # Database command
    subparsers.add_parser('db-stats', help='Show database statistics')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize CLI
    cli = GrowWizCLI()
    
    try:
        await cli.initialize()
        
        # Execute commands
        if args.command == 'monitor':
            cli.monitor_sensors(args.continuous, args.interval)
        
        elif args.command == 'diagnose':
            cli.diagnose_plant(args.image)
        
        elif args.command == 'advice':
            await cli.get_advice(args.question)
        
        elif args.command == 'automation':
            cli.automation_status()
        
        elif args.command == 'test-automation':
            cli.test_automation()
        
        elif args.command == 'scrape':
            await cli.scrape_tips(args.max_pages)
        
        elif args.command == 'db-stats':
            await cli.database_stats()
        
        else:
            print(f"Unknown command: {args.command}")
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\\n\\nOperation cancelled by user")
    
    except Exception as e:
        logger.error(f"CLI error: {e}")
        print(f"Error: {e}")
    
    finally:
        cli.cleanup()

if __name__ == "__main__":
    # Run the CLI
    asyncio.run(main())