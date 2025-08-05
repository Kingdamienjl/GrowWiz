#!/usr/bin/env python3
"""
GrowWiz - AI-powered cultivation assistant
Main application entry point
"""

import os
import asyncio
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
from dotenv import load_dotenv
from loguru import logger

from sensors import SensorManager
from plant_classifier import PlantClassifier
from scraper import GrowTipScraper
from automation import AutomationEngine
from database import DatabaseManager

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="GrowWiz API",
    description="AI-powered cultivation assistant",
    version="1.0.0"
)

# Initialize components
sensor_manager = SensorManager()
plant_classifier = PlantClassifier()
scraper = GrowTipScraper()
automation_engine = AutomationEngine()
db_manager = DatabaseManager()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_startup
async def startup_event():
    """Initialize application components on startup"""
    logger.info("Starting GrowWiz application...")
    
    # Initialize database
    await db_manager.initialize()
    
    # Start background tasks
    asyncio.create_task(sensor_monitoring_loop())
    asyncio.create_task(automation_loop())
    asyncio.create_task(scraping_loop())
    
    logger.info("GrowWiz application started successfully!")

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the main dashboard"""
    with open("static/dashboard.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/api/sensors")
async def get_sensor_data():
    """Get current sensor readings"""
    try:
        data = sensor_manager.read_all_sensors()
        await db_manager.store_sensor_data(data)
        return data
    except Exception as e:
        logger.error(f"Error reading sensors: {e}")
        raise HTTPException(status_code=500, detail="Failed to read sensor data")

@app.post("/api/diagnose")
async def diagnose_plant(file: UploadFile = File(...)):
    """Diagnose plant health from uploaded image"""
    try:
        # Save uploaded file temporarily
        temp_path = f"temp/{file.filename}"
        os.makedirs("temp", exist_ok=True)
        
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Classify the plant
        result = plant_classifier.classify_image(temp_path)
        
        # Clean up temp file
        os.remove(temp_path)
        
        return result
    except Exception as e:
        logger.error(f"Error diagnosing plant: {e}")
        raise HTTPException(status_code=500, detail="Failed to diagnose plant")

@app.get("/api/history")
async def get_history(hours: int = 24):
    """Get historical sensor data"""
    try:
        data = await db_manager.get_sensor_history(hours)
        return data
    except Exception as e:
        logger.error(f"Error retrieving history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve history")

@app.post("/api/advice")
async def get_advice(query: dict):
    """Get AI-powered growing advice"""
    try:
        question = query.get("question", "")
        current_sensors = sensor_manager.read_all_sensors()
        
        # Get relevant tips from scraped data
        tips = await scraper.get_relevant_tips(question)
        
        advice = {
            "question": question,
            "current_conditions": current_sensors,
            "recommendations": tips,
            "timestamp": db_manager.get_timestamp()
        }
        
        return advice
    except Exception as e:
        logger.error(f"Error generating advice: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate advice")

@app.get("/api/automation/status")
async def get_automation_status():
    """Get current automation status"""
    return automation_engine.get_status()

@app.post("/api/automation/toggle")
async def toggle_automation(device: dict):
    """Toggle automation device"""
    device_name = device.get("device")
    state = device.get("state")
    
    try:
        result = automation_engine.toggle_device(device_name, state)
        return {"success": True, "device": device_name, "state": result}
    except Exception as e:
        logger.error(f"Error toggling device {device_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to toggle {device_name}")

async def sensor_monitoring_loop():
    """Background task for continuous sensor monitoring"""
    while True:
        try:
            data = sensor_manager.read_all_sensors()
            await db_manager.store_sensor_data(data)
            logger.debug(f"Sensor data: {data}")
        except Exception as e:
            logger.error(f"Error in sensor monitoring: {e}")
        
        await asyncio.sleep(60)  # Read sensors every minute

async def automation_loop():
    """Background task for automation triggers"""
    while True:
        try:
            sensor_data = sensor_manager.read_all_sensors()
            automation_engine.check_and_trigger(sensor_data)
        except Exception as e:
            logger.error(f"Error in automation loop: {e}")
        
        await asyncio.sleep(30)  # Check automation every 30 seconds

async def scraping_loop():
    """Background task for periodic web scraping"""
    while True:
        try:
            await scraper.scrape_grow_forums()
            logger.info("Completed scraping cycle")
        except Exception as e:
            logger.error(f"Error in scraping loop: {e}")
        
        # Wait for configured interval (default 24 hours)
        interval = int(os.getenv("SCRAPE_INTERVAL_HOURS", 24))
        await asyncio.sleep(interval * 3600)

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8080))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    logger.info(f"Starting GrowWiz server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )