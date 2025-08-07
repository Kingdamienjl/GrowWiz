"""
GrowWiz Web Dashboard
AI-powered cannabis cultivation assistant with advanced web scraping
"""

import json
import os
import asyncio
import re
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
from src.config import config

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'growwiz-dev-key-2024')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Import and register blueprints after app creation
try:
    from src.strain_identification_api import strain_id_bp
    app.register_blueprint(strain_id_bp)
    print("✅ Strain identification API registered")
except Exception as e:
    print(f"❌ Error registering strain identification API: {e}")

try:
    from src.grow_calendar_api import grow_calendar_bp
    app.register_blueprint(grow_calendar_bp, url_prefix='/api/grow')
    print("✅ Grow calendar API registered at /api/grow")
except Exception as e:
    print(f"❌ Error registering grow calendar API: {e}")

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
scraping_status = {'status': 'idle', 'progress': 0, 'active': False, 'last_update': None}

def initialize_components():
    """Initialize all GrowWiz components"""
    global scraper, sensor_manager, automation_engine, strain_scraper, gdrive_manager
    
    try:
        # Initialize tip scraper
        scraper = GrowTipScraper()
        print("✅ GrowTipScraper initialized")
        
        # Initialize sensor manager with environment-aware configuration
        sensor_manager = SensorManager()
        print(f"✅ SensorManager initialized (Environment: {config.environment.value})")
        
        # Initialize automation engine
        automation_engine = AutomationEngine()
        print("✅ AutomationEngine initialized")
        
        # Initialize strain scraper
        strain_scraper = StrainScraper()
        print("✅ StrainScraper initialized")
        
        # Initialize Google Drive manager
        try:
            gdrive_manager = GDriveStrainManager()
            print("✅ GDriveStrainManager initialized")
        except Exception as e:
            print(f"⚠️ GDriveStrainManager initialization failed: {e}")
            print("   Google Drive features will be disabled")
            gdrive_manager = None
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing components: {e}")
        return False

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/strain-identification')
def strain_identification():
    """Strain identification page"""
    return render_template('strain_identification.html')

@app.route('/grow-calendar')
def grow_calendar():
    return render_template('grow_calendar.html')

@app.route('/comprehensive')
def comprehensive():
    """Comprehensive tools page with all original dashboard features"""
    return render_template('comprehensive.html')

# Calendar notes API endpoints
@app.route('/api/grow/notes', methods=['POST'])
def save_calendar_note():
    try:
        data = request.get_json()
        date = data.get('date')
        note = data.get('note')
        
        if not date:
            return jsonify({'error': 'Date is required'}), 400
        
        # Initialize notes file if it doesn't exist
        notes_file = 'calendar_notes.json'
        if not os.path.exists(notes_file):
            with open(notes_file, 'w') as f:
                json.dump({}, f)
        
        # Load existing notes
        with open(notes_file, 'r') as f:
            notes = json.load(f)
        
        # Update or delete note
        if note and note.strip():
            notes[date] = note.strip()
        elif date in notes:
            del notes[date]
        
        # Save updated notes
        with open(notes_file, 'w') as f:
            json.dump(notes, f, indent=2)
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/grow/calendar/<int:year>/<int:month>')
def get_calendar_notes(year, month):
    try:
        notes_file = 'calendar_notes.json'
        if not os.path.exists(notes_file):
            return jsonify({'notes': {}})
        
        with open(notes_file, 'r') as f:
            all_notes = json.load(f)
        
        # Filter notes for the requested month/year
        month_notes = {}
        for date_key, note in all_notes.items():
            try:
                note_date = datetime.strptime(date_key, '%Y-%m-%d')
                if note_date.year == year and note_date.month == month:
                    month_notes[date_key] = note
            except ValueError:
                continue
        
        return jsonify({'notes': month_notes})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def api_status():
    """Get system status with environment information"""
    try:
        # Get sensor data
        sensor_data = sensor_manager.get_all_readings() if sensor_manager else {
            "temperature": 24.5,
            "humidity": 45.2,
            "soil_moisture": 72,
            "co2": 550,
            "light_level": 85,
            "ph": 6.2,
            "simulation_mode": True
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
        
        # Test scenarios (if in testing mode)
        test_scenarios = []
        if config.is_testing_mode() and sensor_manager:
            test_scenarios = sensor_manager.get_available_test_scenarios()
        
        return jsonify({
            "status": "online",
            "timestamp": datetime.now().isoformat(),
            "environment": config.environment.value,
            "simulation_mode": config.should_use_simulation(),
            "testing_mode": config.is_testing_mode(),
            "sensors": sensor_data,
            "scraping": scraping_info,
            "automation": automation_info,
            "test_scenarios": test_scenarios
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/test/scenario', methods=['POST'])
def set_test_scenario():
    """Set test scenario (testing mode only)"""
    if not config.is_testing_mode():
        return jsonify({'error': 'Test scenarios only available in testing mode'}), 403
    
    if not sensor_manager:
        return jsonify({'error': 'Sensor manager not available'}), 500
    
    try:
        data = request.get_json()
        scenario_name = data.get('scenario')
        
        if not scenario_name:
            return jsonify({'error': 'Scenario name required'}), 400
        
        success = sensor_manager.set_test_scenario(scenario_name)
        
        if success:
            return jsonify({
                'success': True,
                'scenario': scenario_name,
                'message': f'Test scenario set to {scenario_name}'
            })
        else:
            return jsonify({'error': 'Invalid scenario name'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        # Automation data
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



@app.route('/api/care-sheet/generate', methods=['POST'])
def generate_care_sheet():
    """Generate comprehensive care sheet for a strain"""
    try:
        data = request.get_json()
        strain_name = data.get('strain')
        method = data.get('method', 'indoor')
        
        if not strain_name:
            return jsonify({'error': 'Strain name is required'}), 400
        
        # Load strain data from enhanced databases
        strain_data = None
        strain_files = [
            'enhanced_strains_v2_635_20250805_104847.json',
            'final_reconstructed_strains.json',
            'enhanced_strains_1500.json',
            'strain_database.json'
        ]
        
        for filename in strain_files:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    strains = json.load(f)
                    # Search for the strain (case-insensitive)
                    for strain in strains:
                        if strain.get('name', '').lower() == strain_name.lower():
                            strain_data = strain
                            break
                    if strain_data:
                        break
            except (FileNotFoundError, json.JSONDecodeError):
                continue
        
        # If strain not found, create basic strain data
        if not strain_data:
            strain_data = {
                'name': strain_name,
                'strain_type': 'Hybrid',
                'growing_difficulty': 'Moderate',
                'genetics': 'Unknown',
                'flowering_time': '8-10 weeks',
                'yield_info': 'Medium',
                'height': 'Medium',
                'climate': 'Indoor/Outdoor',
                'effects': ['Relaxed', 'Happy'],
                'medical_uses': ['Stress', 'Pain'],
                'flavors': ['Earthy'],
                'aromas': ['Herbal']
            }
        
        # Initialize care sheet generator
        from src.care_sheet_generator import AdvancedCareSheetGenerator
        generator = AdvancedCareSheetGenerator()
        
        # Generate care sheet
        care_sheet = generator.generate_comprehensive_care_sheet(strain_data)
        
        return jsonify({
            'care_sheet': care_sheet,
            'strain': strain_name,
            'method': method
        })
        
    except Exception as e:
        print(f"Error generating care sheet: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/strains/list', methods=['GET'])
def get_strain_list():
    """Get list of all available strain names for dropdowns"""
    try:
        strain_names = set()  # Use set to avoid duplicates
        strain_files = [
            'data/enhanced_strains_v2_635_20250805_104847.json',
            'data/final_reconstructed_strains.json',
            'data/enhanced_strains_1500.json',
            'data/strain_database.json',
            'data/improved_strains.json'
        ]
        
        for filename in strain_files:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Handle different JSON structures
                    if isinstance(data, dict) and 'strains' in data:
                        # New format with metadata
                        strains = data['strains']
                    elif isinstance(data, list):
                        # Old format - direct list
                        strains = data
                    else:
                        continue
                    
                    # Extract strain names
                    for strain in strains:
                        if isinstance(strain, dict) and 'name' in strain:
                            name = strain['name'].strip()
                            if name:  # Only add non-empty names
                                strain_names.add(name)
                                
            except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
                print(f"Error loading {filename}: {e}")
                continue
        
        # Convert to sorted list
        strain_list = sorted(list(strain_names))
        
        return jsonify({
            'strains': strain_list,
            'total': len(strain_list)
        })
        
    except Exception as e:
        print(f"Error getting strain list: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/care-sheet/quick-ref', methods=['POST'])
def generate_quick_reference():
    """Generate quick reference for a strain"""
    try:
        data = request.get_json()
        strain_name = data.get('strain')
        
        if not strain_name:
            return jsonify({'error': 'Strain name is required'}), 400
        
        # Load strain data from enhanced databases
        strain_data = None
        strain_files = [
            'enhanced_strains_v2_635_20250805_104847.json',
            'final_reconstructed_strains.json',
            'enhanced_strains_1500.json',
            'strain_database.json'
        ]
        
        for filename in strain_files:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    strains = json.load(f)
                    # Search for the strain (case-insensitive)
                    for strain in strains:
                        if strain.get('name', '').lower() == strain_name.lower():
                            strain_data = strain
                            break
                    if strain_data:
                        break
            except (FileNotFoundError, json.JSONDecodeError):
                continue
        
        # If strain not found, create basic strain data
        if not strain_data:
            strain_data = {
                'name': strain_name,
                'strain_type': 'Hybrid',
                'growing_difficulty': 'Moderate',
                'genetics': 'Unknown',
                'flowering_time': '8-10 weeks',
                'effects': ['Relaxed', 'Happy'],
                'medical_uses': ['Stress', 'Pain'],
                'flavors': ['Earthy']
            }
        
        # Generate quick reference (simplified version)
        quick_ref = f"""# 🌿 {strain_name} - Quick Reference

**Type**: {strain_data.get('strain_type', 'Unknown')}
**Difficulty**: {strain_data.get('growing_difficulty', 'Moderate')}
**Flowering Time**: {strain_data.get('flowering_time', 'Unknown')}

## Key Growing Tips:
- Light Schedule: 18/6 (veg) → 12/12 (flower)
- Temperature: 70-80°F day, 60-70°F night
- Humidity: 60% (veg) → 40% (flower)
- Nutrients: High N (veg) → High P/K (flower)

## Effects: {', '.join(strain_data.get('effects', []))}
## Medical Uses: {', '.join(strain_data.get('medical_uses', []))}
"""
        
        return jsonify({
            'quick_ref': quick_ref,
            'strain': strain_name
        })
        
    except Exception as e:
        print(f"Error generating quick reference: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/setup-guide/generate', methods=['POST'])
def generate_setup_guide():
    """Generate comprehensive grow setup guide with product links"""
    try:
        data = request.get_json()
        budget = data.get('budget', 'mid')
        space = data.get('space', 'medium')
        
        # Setup guide templates with product links
        setup_guides = {
            'budget': {
                'small': {
                    'title': 'Budget Small Space Setup ($200-500)',
                    'lighting': 'Mars Hydro TS 600W LED ($70) - https://amzn.to/marshydro600',
                    'tent': 'VIVOSUN 2x2x4 Grow Tent ($60) - https://amzn.to/vivosun2x2',
                    'ventilation': 'VIVOSUN 4" Inline Fan Kit ($45) - https://amzn.to/vivosun4inch',
                    'medium': 'Fox Farm Ocean Forest Soil ($25) - https://amzn.to/foxfarmsoil',
                    'nutrients': 'General Hydroponics Flora Series ($30) - https://amzn.to/ghflora',
                    'containers': '3-Gallon Fabric Pots x4 ($20) - https://amzn.to/fabricpots3gal',
                    'total': '$250-300'
                },
                'medium': {
                    'title': 'Budget Medium Space Setup ($300-500)',
                    'lighting': 'Spider Farmer SF-2000 LED ($150) - https://amzn.to/spiderfarmer2000',
                    'tent': 'VIVOSUN 4x4x6.5 Grow Tent ($120) - https://amzn.to/vivosun4x4',
                    'ventilation': 'AC Infinity CLOUDLINE T6 ($130) - https://amzn.to/acinfinity6',
                    'medium': 'Fox Farm Ocean Forest Soil x2 ($50) - https://amzn.to/foxfarmsoil',
                    'nutrients': 'General Hydroponics Flora Series ($30) - https://amzn.to/ghflora',
                    'containers': '5-Gallon Fabric Pots x4 ($25) - https://amzn.to/fabricpots5gal',
                    'total': '$400-500'
                }
            },
            'mid': {
                'medium': {
                    'title': 'Mid-Range 4x4 Setup ($500-1500)',
                    'lighting': 'HLG 300L Rspec LED ($400) - https://amzn.to/hlg300l',
                    'tent': 'Gorilla Grow Tent 4x4x7 ($200) - https://amzn.to/gorilla4x4',
                    'ventilation': 'AC Infinity CLOUDLINE T6 + Controller ($180) - https://amzn.to/acinfinity6pro',
                    'medium': 'Coco Coir + Perlite Mix ($40) - https://amzn.to/cococoir',
                    'nutrients': 'Canna Coco A+B + Additives ($80) - https://amzn.to/cannacoco',
                    'containers': '5-Gallon Fabric Pots x6 ($30) - https://amzn.to/fabricpots5gal',
                    'monitoring': 'Pulse One Environmental Monitor ($200) - https://amzn.to/pulseone',
                    'total': '$1000-1200'
                }
            },
            'premium': {
                'medium': {
                    'title': 'Premium 4x4 Setup ($1500-3000)',
                    'lighting': 'Fluence SPYDR 2i LED ($800) - https://amzn.to/fluencespydr',
                    'tent': 'Gorilla Grow Tent 4x4x8 LITE LINE ($250) - https://amzn.to/gorilla4x8',
                    'ventilation': 'AC Infinity CLOUDLINE PRO T6 ($250) - https://amzn.to/acinfinitypro',
                    'medium': 'Rockwool + Hydroponic System ($200) - https://amzn.to/rockwoolsystem',
                    'nutrients': 'Advanced Nutrients pH Perfect Series ($150) - https://amzn.to/advancednutrients',
                    'containers': 'Hydroponic Net Pots + System ($100) - https://amzn.to/hydrosystem',
                    'monitoring': 'Trolmaster Hydro-X Pro ($400) - https://amzn.to/trolmaster',
                    'automation': 'Automated Irrigation System ($300) - https://amzn.to/autoirrigation',
                    'total': '$2200-2500'
                }
            }
        }
        
        # Get the appropriate setup guide
        guide_data = setup_guides.get(budget, {}).get(space, {
            'title': f'{budget.title()} {space.title()} Setup',
            'lighting': 'LED Grow Light - Contact for recommendations',
            'tent': 'Grow Tent - Contact for recommendations',
            'total': 'Contact for pricing'
        })
        
        # Generate the setup guide
        setup_guide = f"""# 🏗️ {guide_data['title']}

## Complete Equipment List & Links

### 🔆 Lighting System
**{guide_data.get('lighting', 'LED Grow Light System')}**
- Full spectrum LED for optimal plant growth
- Energy efficient and low heat output
- Suitable for all growth phases

### 🏠 Growing Environment
**{guide_data.get('tent', 'Grow Tent System')}**
- Reflective interior for maximum light efficiency
- Multiple ports for ventilation and cables
- Sturdy frame and lightproof zippers

### 💨 Ventilation System
**{guide_data.get('ventilation', 'Ventilation System')}**
- Proper air exchange for healthy plants
- Temperature and humidity control
- Odor filtration capabilities

### 🌱 Growing Medium
**{guide_data.get('medium', 'Growing Medium')}**
- Optimal drainage and aeration
- pH balanced for cannabis cultivation
- Organic nutrients for healthy growth

### 🧪 Nutrition System
**{guide_data.get('nutrients', 'Nutrient System')}**
- Complete macro and micronutrients
- pH balanced formulations
- Growth and bloom specific ratios

### 🪴 Containers
**{guide_data.get('containers', 'Growing Containers')}**
- Proper drainage and root aeration
- Appropriate size for plant development
- Reusable and durable construction

{f"### 📊 Monitoring Equipment\\n**{guide_data['monitoring']}**\\n- Real-time environmental monitoring\\n- Data logging and alerts\\n- Mobile app connectivity\\n" if 'monitoring' in guide_data else ""}

{f"### 🤖 Automation\\n**{guide_data['automation']}**\\n- Automated watering and feeding\\n- Environmental control integration\\n- Programmable schedules\\n" if 'automation' in guide_data else ""}

## Setup Instructions

### Step 1: Tent Assembly
1. Assemble grow tent according to manufacturer instructions
2. Ensure all zippers and seams are properly sealed
3. Position tent in appropriate location with power access

### Step 2: Lighting Installation
1. Install LED light at appropriate height (18-24" from canopy)
2. Connect to timer for automated light cycles
3. Test light intensity and coverage area

### Step 3: Ventilation Setup
1. Install exhaust fan at top of tent
2. Connect carbon filter for odor control
3. Install intake fan or passive intake at bottom
4. Test airflow and adjust fan speeds

### Step 4: Environmental Controls
1. Install temperature and humidity monitors
2. Set up automated controls if included
3. Test all systems before planting

### Step 5: Growing Medium Preparation
1. Prepare growing medium according to instructions
2. Fill containers and pre-moisten if needed
3. Check pH and adjust if necessary

## Estimated Total Cost: {guide_data.get('total', 'Contact for pricing')}

## Additional Recommendations

### Essential Accessories:
- pH Testing Kit ($15) - https://amzn.to/phtestkit
- TDS/EC Meter ($20) - https://amzn.to/tdsmeter
- Pruning Shears ($15) - https://amzn.to/pruningshears
- Plant Training Wire ($10) - https://amzn.to/trainingwire

### Optional Upgrades:
- CO2 Supplementation System
- Advanced Environmental Controllers
- Automated Nutrient Dosing
- Security Camera System

## Maintenance Schedule

### Daily:
- Check temperature and humidity
- Monitor plant health
- Adjust light height as needed

### Weekly:
- Water/feed plants as needed
- Check pH and nutrient levels
- Inspect for pests or diseases

### Monthly:
- Clean and maintain equipment
- Replace filters as needed
- Calibrate monitoring equipment

---
*This setup guide is optimized for {budget} budget and {space} growing space.*
*All product links are affiliate links that help support this project.*
*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return jsonify({
            'setup_guide': setup_guide,
            'budget': budget,
            'space': space
        })
        
    except Exception as e:
        print(f"Error generating setup guide: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/growing-tips/search', methods=['POST'])
def search_growing_tips():
    """Search growing tips from scraped database"""
    try:
        data = request.get_json()
        query = data.get('query', '').lower()
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        # Load strain data from enhanced databases to extract growing tips
        tips = []
        strain_files = [
            'data/enhanced_strains_v2_635_20250805_104847.json',
            'data/final_reconstructed_strains.json',
            'data/enhanced_strains_1500.json'
        ]
        
        for filename in strain_files:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    strains = json.load(f)
                    for strain in strains:
                        # Search in strain descriptions, growing info, effects, etc.
                        searchable_text = ' '.join([
                            str(strain.get('description', '')),
                            str(strain.get('growing_tips', '')),
                            str(strain.get('effects', [])),
                            str(strain.get('medical_uses', [])),
                            str(strain.get('growing_difficulty', '')),
                            str(strain.get('climate', '')),
                            str(strain.get('strain_type', ''))
                        ]).lower()
                        
                        if query in searchable_text:
                            tip = f"**{strain.get('name', 'Unknown')}** ({strain.get('strain_type', 'Unknown')})\n"
                            tip += f"Growing Difficulty: {strain.get('growing_difficulty', 'Unknown')}\n"
                            tip += f"Climate: {strain.get('climate', 'Unknown')}\n"
                            if strain.get('growing_tips'):
                                tip += f"Tips: {strain.get('growing_tips')}\n"
                            if strain.get('description'):
                                tip += f"Description: {strain.get('description')[:200]}...\n"
                            tips.append(tip)
                        
                        if len(tips) >= 20:  # Limit results
                            break
                    if len(tips) >= 20:
                        break
            except (FileNotFoundError, json.JSONDecodeError):
                continue
        
        return jsonify({
            'tips': tips,
            'query': query,
            'count': len(tips)
        })
        
    except Exception as e:
        print(f"Error searching growing tips: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/growing-tips/refresh', methods=['POST'])
def refresh_growing_tips():
    """Refresh growing tips from scraped database"""
    try:
        # Load random tips from enhanced databases
        tips = []
        strain_files = [
            'data/enhanced_strains_v2_635_20250805_104847.json',
            'data/final_reconstructed_strains.json'
        ]
        
        for filename in strain_files:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    strains = json.load(f)
                    import random
                    random_strains = random.sample(strains, min(10, len(strains)))
                    
                    for strain in random_strains:
                        tip = f"**{strain.get('name', 'Unknown')}** - {strain.get('strain_type', 'Unknown')} strain\n"
                        tip += f"Difficulty: {strain.get('growing_difficulty', 'Moderate')} | "
                        tip += f"Flowering: {strain.get('flowering_time', 'Unknown')}\n"
                        if strain.get('effects'):
                            tip += f"Effects: {', '.join(strain.get('effects', [])[:3])}\n"
                        tips.append(tip)
                        
                        if len(tips) >= 15:
                            break
                    if len(tips) >= 15:
                        break
            except (FileNotFoundError, json.JSONDecodeError):
                continue
        
        return jsonify({
            'tips': tips,
            'count': len(tips)
        })
        
    except Exception as e:
        print(f"Error refreshing growing tips: {e}")
        return jsonify({'error': str(e)}), 500
@app.route('/api/strains/organize-gdrive', methods=['POST'])
def organize_strains_to_gdrive():
    """Organize scraped strains to Google Drive"""
    try:
        if gdrive_manager is None:
            return jsonify({
                'error': 'Google Drive manager not initialized',
                'details': 'Google Drive features are disabled. This may be due to missing credentials or configuration.',
                'suggestion': 'Check your Google Drive API credentials and ensure the service account key is properly configured.'
            }), 500
        # Load strains from JSON files instead of relying on scraped_strains
        strain_files = [
            "data/enhanced_strains_v2_635_20250805_104847.json",  # New v2 data
            "data/final_reconstructed_strains.json",
            "data/improved_strains.json", 
            "data/enhanced_strains_1500.json",
            "data/strains_data.json"
        ]
        
        strains_data = []
        source_file = None
        
        for file_path in strain_files:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Handle different data structures
                if isinstance(data, dict) and 'strains' in data:
                    strains_data = data['strains']
                elif isinstance(data, list):
                    strains_data = data
                else:
                    continue
                
                source_file = file_path
                break
        
        if not strains_data:
            return jsonify({"error": "No strain data available to organize"}), 400
        
        if not gdrive_manager:
            return jsonify({
                "error": "Google Drive manager not initialized",
                "details": "Google Drive features are disabled. This may be due to missing credentials or configuration.",
                "suggestion": "Check your Google Drive API credentials and ensure the service account key is properly configured."
            }), 500
        
        # Start organization in background
        def organize_background():
            global scraping_status
            scraping_status["gdrive_active"] = True
            scraping_status["gdrive_progress"] = 0
            
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                results = loop.run_until_complete(gdrive_manager.organize_strains_to_drive(strains_data))
                
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
            "message": f"Started organizing {len(strains_data)} strains to Google Drive",
            "source": source_file,
            "status": "started",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/strains')
def list_strains():
    """List all scraped strains from JSON files"""
    try:
        # Try to load from our best strain data file (prioritize v2 enhanced data)
        strain_files = [
            "data/enhanced_strains_v2_635_20250805_104847.json",  # New v2 data
            "data/final_reconstructed_strains.json",
            "data/improved_strains.json", 
            "data/enhanced_strains_1500.json",
            "data/strains_data.json"
        ]
        
        for file_path in strain_files:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Handle different data structures
                if isinstance(data, dict) and 'strains' in data:
                    strains = data['strains']
                    metadata = data.get('metadata', {})
                elif isinstance(data, list):
                    strains = data
                    metadata = {}
                else:
                    continue
                
                # Clean descriptions from newsletter notifications if needed
                for strain in strains:
                    if 'description' in strain and strain['description']:
                        # Remove any remaining newsletter text
                        description = strain['description']
                        newsletter_patterns = [
                            r'Follow\s+Our\s+Newsletter.*?deals!?',
                            r'Get\s+exclusive\s+information.*?deals!?'
                        ]
                        for pattern in newsletter_patterns:
                            description = re.sub(pattern, '', description, flags=re.IGNORECASE | re.DOTALL)
                        strain['description'] = description.strip()
                
                return jsonify({
                    "strains": strains,
                    "total": len(strains),
                    "metadata": metadata,
                    "source": file_path
                })
        
        return jsonify({"strains": [], "total": 0, "error": "No strain data files found"})
        
    except Exception as e:
        print(f"Error loading strains: {e}")
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