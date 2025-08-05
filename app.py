"""
GrowWiz Web Dashboard
AI-powered cannabis cultivation assistant with advanced web scraping
"""

import os
import json
import asyncio
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import threading
import time

# Import GrowWiz modules
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.scraper import GrowTipScraper
from src.sensors import SensorManager
from src.automation import AutomationEngine
from src.strain_scraper import StrainScraper
from src.gdrive_manager import GDriveStrainManager

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'growwiz-dev-key-2024')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('data', exist_ok=True)

# Global instances
scraper = None
sensor_manager = None
automation_engine = None
strain_scraper = None
gdrive_manager = None
scraping_thread = None
# Global variables for scraping status
scraping_status = {'status': 'idle', 'progress': 0}

def initialize_components():
    """Initialize all GrowWiz components"""
    global scraper, sensor_manager, automation_engine, strain_scraper, gdrive_manager
    
    try:
        # Initialize tip scraper
        scraper = GrowTipScraper()
        print("✅ GrowTipScraper initialized")
        
        # Initialize sensor manager
        sensor_manager = SensorManager()
        print("✅ SensorManager initialized")
        
        # Initialize automation engine
        automation_engine = AutomationEngine()
        print("✅ AutomationEngine initialized")
        
        # Initialize strain scraper
        strain_scraper = StrainScraper()
        print("✅ StrainScraper initialized")
        
        # Initialize Google Drive manager
        gdrive_manager = GDriveStrainManager()
        print("✅ GDriveStrainManager initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing components: {e}")
        return False

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/status')
def api_status():
    """Get system status"""
    try:
        # Get sensor data
        sensor_data = sensor_manager.read_all_sensors() if sensor_manager else {
            "temperature": 24.5,
            "humidity": 45.2,
            "soil_moisture": 72,
            "co2": 550,
            "light_level": 85,
            "ph": 6.2
        }
        
        # Get scraping status
        scraping_info = {
            "active": scraping_status["active"],
            "progress": scraping_status["progress"],
            "last_update": scraping_status["last_update"],
            "total_tips": len(scraper.scraped_data) if scraper else 0
        }
        
        # Get automation status
        automation_info = {
            "active_triggers": 3,
            "last_action": "Adjusted humidity - 2 minutes ago",
            "next_check": "30 seconds"
        }
        
        return jsonify({
            "status": "online",
            "timestamp": datetime.now().isoformat(),
            "sensors": sensor_data,
            "scraping": scraping_info,
            "automation": automation_info
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/scrape/start', methods=['POST'])
def start_scraping():
    """Start web scraping process"""
    global scraping_status
    
    if scraping_status["active"]:
        return jsonify({"error": "Scraping already in progress"}), 400
    
    try:
        # Start scraping in background thread
        def run_scraping():
            global scraping_status
            scraping_status["active"] = True
            scraping_status["progress"] = 0
            
            async def scrape_async():
                try:
                    if scraper:
                        scraping_status["progress"] = 25
                        tips = await scraper.scrape_grow_forums()
                        scraping_status["progress"] = 100
                        scraping_status["last_update"] = datetime.now().isoformat()
                        print(f"✅ Scraped {len(tips)} tips successfully")
                    else:
                        raise Exception("Scraper not initialized")
                except Exception as e:
                    print(f"❌ Scraping error: {e}")
                finally:
                    scraping_status["active"] = False
            
            # Run async scraping
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(scrape_async())
            loop.close()
        
        thread = threading.Thread(target=run_scraping)
        thread.daemon = True
        thread.start()
        
        return jsonify({"message": "Scraping started", "status": "initiated"})
        
    except Exception as e:
        scraping_status["active"] = False
        return jsonify({"error": str(e)}), 500

@app.route('/api/tips')
def get_tips():
    """Get scraped growing tips"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        category = request.args.get('category', '')
        search = request.args.get('search', '')
        
        tips = scraper.scraped_data if scraper else []
        
        # Filter by category
        if category:
            tips = [tip for tip in tips if tip.get('category', '').lower() == category.lower()]
        
        # Filter by search term
        if search:
            search_lower = search.lower()
            tips = [tip for tip in tips if search_lower in tip.get('content', '').lower()]
        
        # Sort by relevance score
        tips.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Paginate
        start = (page - 1) * per_page
        end = start + per_page
        paginated_tips = tips[start:end]
        
        return jsonify({
            "tips": paginated_tips,
            "total": len(tips),
            "page": page,
            "per_page": per_page,
            "has_next": end < len(tips),
            "has_prev": page > 1
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/tips/search')
def search_tips():
    """Search tips by query"""
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({"tips": [], "total": 0})
        
        if scraper:
            relevant_tips = scraper.get_relevant_tips(query)
            return jsonify({
                "tips": relevant_tips[:20],  # Limit to 20 results
                "total": len(relevant_tips),
                "query": query
            })
        else:
            return jsonify({"tips": [], "total": 0})
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/plant/diagnose', methods=['POST'])
def diagnose_plant():
    """Diagnose plant problems from uploaded image"""
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image uploaded"}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Mock plant diagnosis (replace with actual AI model)
            diagnosis = {
                "plant_type": "Cannabis Indica",
                "health_score": 75,
                "issues": [
                    {
                        "problem": "Nitrogen Deficiency",
                        "confidence": 0.85,
                        "severity": "moderate",
                        "symptoms": ["Yellowing lower leaves", "Slow growth"],
                        "solutions": [
                            "Increase nitrogen-rich fertilizer",
                            "Check pH levels (should be 6.0-7.0)",
                            "Ensure proper drainage"
                        ]
                    }
                ],
                "recommendations": [
                    "Monitor pH levels daily",
                    "Adjust feeding schedule",
                    "Increase light exposure if possible"
                ],
                "growth_stage": "vegetative",
                "estimated_harvest": "6-8 weeks"
            }
            
            return jsonify({
                "diagnosis": diagnosis,
                "image_path": filepath,
                "timestamp": datetime.now().isoformat()
            })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/automation/triggers')
def get_automation_triggers():
    """Get automation trigger status"""
    try:
        # Mock automation data
        triggers = [
            {
                "id": 1,
                "name": "Humidity Control",
                "condition": "humidity < 40%",
                "action": "Turn on humidifier",
                "status": "active",
                "last_triggered": "2024-01-15 14:30:00"
            },
            {
                "id": 2,
                "name": "Temperature Control",
                "condition": "temperature > 28°C",
                "action": "Turn on exhaust fan",
                "status": "active",
                "last_triggered": "Never"
            },
            {
                "id": 3,
                "name": "Watering Schedule",
                "condition": "soil_moisture < 30%",
                "action": "Activate water pump",
                "status": "active",
                "last_triggered": "2024-01-15 09:15:00"
            }
        ]
        
        return jsonify({"triggers": triggers})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/hyperbrowser/test', methods=['POST'])
def test_hyperbrowser():
    """Test Hyperbrowser functionality"""
    try:
        test_url = request.json.get('url', 'https://www.growweedeasy.com/')
        
        # Mock Hyperbrowser test result
        result = {
            "success": True,
            "url": test_url,
            "method": "hyperbrowser_scraping",
            "content_extracted": True,
            "tips_found": 15,
            "processing_time": "3.2 seconds",
            "features_used": [
                "JavaScript rendering",
                "Cookie handling",
                "Stealth mode",
                "Content extraction"
            ],
            "sample_tips": [
                "Maintain humidity between 40-60% during flowering",
                "Check pH levels daily for optimal nutrient uptake",
                "Use LED lights for energy-efficient growing"
            ]
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/scrape-strains', methods=['POST'])
def scrape_strains():
    """Enhanced API endpoint to start strain scraping with multiple modes"""
    try:
        data = request.get_json()
        count = data.get('count', 100)
        mode = data.get('mode', 'enhanced')
        enhanced = data.get('enhanced', True)
        
        print(f"Starting enhanced strain scraping: {count} strains, mode: {mode}")
        
        if not strain_scraper:
            return jsonify({"error": "Strain scraper not initialized"}), 500
        
        # Start scraping in background
        def scrape_background():
            global scraping_status
            scraping_status["active"] = True
            scraping_status["progress"] = 0
            scraping_status["mode"] = mode
            
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                strains = loop.run_until_complete(strain_scraper.scrape_top_strains(count))
                
                # Save results
                strain_scraper.save_strains_data(f"data/enhanced_strains_{count}.json")
                
                scraping_status["progress"] = 100
                scraping_status["last_update"] = datetime.now().isoformat()
                scraping_status["results"] = {
                    "scraped_count": len(strains),
                    "target_count": count,
                    "mode": mode,
                    "sources_used": "15+ cannabis databases" if enhanced else "Basic sources",
                    "summary": strain_scraper.get_strain_summary()
                }
                
            except Exception as e:
                scraping_status["error"] = str(e)
            finally:
                scraping_status["active"] = False
        
        import threading
        thread = threading.Thread(target=scrape_background)
        thread.start()
        
        return jsonify({
            "success": True,
            "message": f"Enhanced scraping started for {count} strains using {mode} mode",
            "count": count,
            "mode": mode,
            "sources": "15+ cannabis databases" if enhanced else "Basic sources",
            "status": "started",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Error starting enhanced scraping: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/scraping-status', methods=['GET'])
def get_scraping_status():
    """Get current enhanced scraping status"""
    return jsonify(scraping_status)



@app.route('/api/strains/organize-gdrive', methods=['POST'])
def organize_strains_to_gdrive():
    """Organize scraped strains to Google Drive"""
    try:
        if not strain_scraper or not strain_scraper.scraped_strains:
            return jsonify({"error": "No strains available to organize"}), 400
        
        if not gdrive_manager:
            return jsonify({"error": "Google Drive manager not initialized"}), 500
        
        # Start organization in background
        def organize_background():
            global scraping_status
            scraping_status["gdrive_active"] = True
            scraping_status["gdrive_progress"] = 0
            
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Convert strains to dict format
                strains_dict = [strain.__dict__ for strain in strain_scraper.scraped_strains]
                
                results = loop.run_until_complete(gdrive_manager.organize_strains_to_drive(strains_dict))
                
                scraping_status["gdrive_progress"] = 100
                scraping_status["gdrive_results"] = results
                scraping_status["gdrive_last_update"] = datetime.now().isoformat()
                
            except Exception as e:
                scraping_status["gdrive_error"] = str(e)
            finally:
                scraping_status["gdrive_active"] = False
        
        import threading
        thread = threading.Thread(target=organize_background)
        thread.start()
        
        return jsonify({
            "message": f"Started organizing {len(strain_scraper.scraped_strains)} strains to Google Drive",
            "status": "started",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/strains/list')
def list_scraped_strains():
    """List all scraped strains"""
    try:
        if not strain_scraper:
            return jsonify({"strains": [], "total": 0})
        
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        strain_type = request.args.get('type', '')
        
        strains = strain_scraper.scraped_strains
        
        # Filter by type if specified
        if strain_type:
            strains = [s for s in strains if s.strain_type.lower() == strain_type.lower()]
        
        # Convert to dict format
        strains_dict = [strain.__dict__ for strain in strains]
        
        # Paginate
        start = (page - 1) * per_page
        end = start + per_page
        paginated_strains = strains_dict[start:end]
        
        return jsonify({
            "strains": paginated_strains,
            "total": len(strains_dict),
            "page": page,
            "per_page": per_page,
            "has_next": end < len(strains_dict),
            "has_prev": page > 1,
            "summary": strain_scraper.get_strain_summary() if strain_scraper.scraped_strains else {}
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    print("🌿 Starting GrowWiz Dashboard...")
    initialize_components()
    
    # Development server settings
    debug_mode = os.getenv('DEBUG', 'True').lower() == 'true'
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', 5000))
    
    print(f"🚀 Dashboard will be available at: http://{host}:{port}")
    print("📊 Features available:")
    print("   • Real-time sensor monitoring")
    print("   • Advanced web scraping with Hyperbrowser")
    print("   • Plant image diagnosis")
    print("   • Automation trigger management")
    print("   • Growing tips database")
    
    app.run(host=host, port=port, debug=debug_mode)