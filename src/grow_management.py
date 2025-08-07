"""
Comprehensive Grow Management System
Handles grow prerequisites, product lists, chemical guides, schedules, and tracking
"""

import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class GrowType(Enum):
    """Types of grow cycles"""
    AUTOFLOWER = "autoflower"
    PHOTOPERIOD_SEED = "photoperiod_seed"
    PHOTOPERIOD_CLONE = "photoperiod_clone"
    FEMINIZED_SEED = "feminized_seed"

class GrowPhase(Enum):
    """Growing phases"""
    GERMINATION = "germination"
    SEEDLING = "seedling"
    VEGETATIVE = "vegetative"
    PRE_FLOWER = "pre_flower"
    FLOWERING = "flowering"
    HARVEST = "harvest"
    CURING = "curing"

@dataclass
class Product:
    """Represents a grow product/supply"""
    name: str
    category: str
    brand: str
    price_range: str
    description: str
    required: bool
    phase: List[str]
    alternatives: List[str]

@dataclass
class Chemical:
    """Represents a nutrient or chemical"""
    name: str
    type: str  # nutrient, supplement, ph_adjuster, etc.
    npk_ratio: Optional[str]
    concentration: str
    usage_rate: str
    mixing_instructions: str
    compatibility: List[str]
    warnings: List[str]

@dataclass
class WeeklySchedule:
    """Weekly grow schedule"""
    week: int
    phase: GrowPhase
    light_schedule: str
    temperature_day: str
    temperature_night: str
    humidity: str
    nutrients: List[Dict[str, Any]]
    watering_frequency: str
    tasks: List[str]
    notes: str

@dataclass
class GrowSession:
    """Represents an active grow session"""
    id: str
    strain_name: str
    grow_type: GrowType
    start_date: datetime
    current_week: int
    current_phase: GrowPhase
    expected_harvest: datetime
    notes: str
    active: bool

class GrowManagementSystem:
    """Comprehensive grow management system"""
    
    def __init__(self):
        self.products = self._initialize_products()
        self.chemicals = self._initialize_chemicals()
        self.grow_schedules = self._initialize_schedules()
        self.active_sessions = []
    
    def _initialize_products(self) -> Dict[str, List[Product]]:
        """Initialize comprehensive product database"""
        return {
            "lighting": [
                Product(
                    name="LED Full Spectrum Grow Light",
                    category="lighting",
                    brand="Spider Farmer/Mars Hydro",
                    price_range="$100-300",
                    description="Full spectrum LED with dimmer control, 100-300W",
                    required=True,
                    phase=["all"],
                    alternatives=["HPS", "CMH", "T5 Fluorescent"]
                ),
                Product(
                    name="Timer Controller",
                    category="lighting",
                    brand="Various",
                    price_range="$15-50",
                    description="Digital timer for light scheduling",
                    required=True,
                    phase=["all"],
                    alternatives=["Smart plugs", "Mechanical timers"]
                )
            ],
            "ventilation": [
                Product(
                    name="Inline Exhaust Fan",
                    category="ventilation",
                    brand="AC Infinity/Vivosun",
                    price_range="$50-150",
                    description="4-6 inch inline fan with speed controller",
                    required=True,
                    phase=["all"],
                    alternatives=["Bathroom fans", "Computer fans"]
                ),
                Product(
                    name="Carbon Filter",
                    category="ventilation",
                    brand="Phresh/Can-Lite",
                    price_range="$40-100",
                    description="Activated carbon filter for odor control",
                    required=True,
                    phase=["flowering", "harvest"],
                    alternatives=["ONA gel", "Air purifiers"]
                ),
                Product(
                    name="Oscillating Fan",
                    category="ventilation",
                    brand="Various",
                    price_range="$20-60",
                    description="6-8 inch clip-on fan for air circulation",
                    required=True,
                    phase=["all"],
                    alternatives=["Desktop fans", "Tower fans"]
                )
            ],
            "growing_medium": [
                Product(
                    name="Coco Coir",
                    category="growing_medium",
                    brand="Canna/Mother Earth",
                    price_range="$15-30",
                    description="Compressed coco coir bricks, pH buffered",
                    required=False,
                    phase=["all"],
                    alternatives=["Soil", "Perlite mix", "Rockwool"]
                ),
                Product(
                    name="Premium Potting Soil",
                    category="growing_medium",
                    brand="Fox Farm/Roots Organic",
                    price_range="$20-40",
                    description="Pre-mixed organic potting soil",
                    required=False,
                    phase=["all"],
                    alternatives=["Coco coir", "Hydroponic systems"]
                ),
                Product(
                    name="Perlite",
                    category="growing_medium",
                    brand="Various",
                    price_range="$10-20",
                    description="Volcanic glass for drainage and aeration",
                    required=False,
                    phase=["all"],
                    alternatives=["Vermiculite", "Pumice"]
                )
            ],
            "containers": [
                Product(
                    name="Fabric Pots",
                    category="containers",
                    brand="Smart Pots/Vivosun",
                    price_range="$5-25",
                    description="3-7 gallon fabric grow bags",
                    required=True,
                    phase=["vegetative", "flowering"],
                    alternatives=["Plastic pots", "Air pots"]
                ),
                Product(
                    name="Seedling Trays",
                    category="containers",
                    brand="Various",
                    price_range="$10-20",
                    description="72-cell seedling starter trays",
                    required=True,
                    phase=["germination", "seedling"],
                    alternatives=["Solo cups", "Jiffy pots"]
                )
            ],
            "monitoring": [
                Product(
                    name="Digital Thermometer/Hygrometer",
                    category="monitoring",
                    brand="AcuRite/ThermoPro",
                    price_range="$10-30",
                    description="Digital temp/humidity monitor with min/max",
                    required=True,
                    phase=["all"],
                    alternatives=["Analog gauges", "Smart sensors"]
                ),
                Product(
                    name="pH Meter",
                    category="monitoring",
                    brand="Apera/Bluelab",
                    price_range="$30-100",
                    description="Digital pH meter with calibration solutions",
                    required=True,
                    phase=["all"],
                    alternatives=["pH test strips", "Liquid pH test kit"]
                ),
                Product(
                    name="TDS/EC Meter",
                    category="monitoring",
                    brand="Apera/Bluelab",
                    price_range="$20-80",
                    description="Total dissolved solids/electrical conductivity meter",
                    required=True,
                    phase=["vegetative", "flowering"],
                    alternatives=["Combo pH/TDS meters"]
                )
            ]
        }
    
    def _initialize_chemicals(self) -> Dict[str, List[Chemical]]:
        """Initialize comprehensive chemical/nutrient database"""
        return {
            "base_nutrients": [
                Chemical(
                    name="General Hydroponics Flora Series",
                    type="base_nutrient",
                    npk_ratio="Variable (3-part system)",
                    concentration="Liquid concentrate",
                    usage_rate="2-4ml per liter",
                    mixing_instructions="Mix FloraGro, FloraMicro, FloraBloom in recommended ratios",
                    compatibility=["Most supplements", "pH adjusters"],
                    warnings=["Store in cool, dark place", "Shake before use"]
                ),
                Chemical(
                    name="Advanced Nutrients pH Perfect",
                    type="base_nutrient",
                    npk_ratio="Variable (3-part system)",
                    concentration="Liquid concentrate",
                    usage_rate="4ml per liter",
                    mixing_instructions="Mix Grow, Micro, Bloom in equal parts",
                    compatibility=["AN supplements", "Most additives"],
                    warnings=["pH Perfect technology - minimal pH adjustment needed"]
                )
            ],
            "supplements": [
                Chemical(
                    name="Cal-Mag Plus",
                    type="supplement",
                    npk_ratio="1-0-0",
                    concentration="Liquid concentrate",
                    usage_rate="1-5ml per liter",
                    mixing_instructions="Add first to water, then base nutrients",
                    compatibility=["All nutrient lines"],
                    warnings=["Essential for coco coir and RO water"]
                ),
                Chemical(
                    name="Silica Supplement",
                    type="supplement",
                    npk_ratio="0-0-3",
                    concentration="Liquid concentrate",
                    usage_rate="0.5-1ml per liter",
                    mixing_instructions="Add first to water, mix thoroughly before other nutrients",
                    compatibility=["Most nutrients (add first)"],
                    warnings=["Can cause precipitation if mixed incorrectly"]
                )
            ],
            "ph_adjusters": [
                Chemical(
                    name="pH Down (Phosphoric Acid)",
                    type="ph_adjuster",
                    npk_ratio="0-0-0",
                    concentration="85% phosphoric acid",
                    usage_rate="0.5-2ml per liter",
                    mixing_instructions="Add drop by drop, mix and test",
                    compatibility=["All nutrient solutions"],
                    warnings=["Corrosive - wear gloves", "Store safely away from children"]
                ),
                Chemical(
                    name="pH Up (Potassium Hydroxide)",
                    type="ph_adjuster",
                    npk_ratio="0-0-0",
                    concentration="Potassium hydroxide solution",
                    usage_rate="0.5-2ml per liter",
                    mixing_instructions="Add drop by drop, mix and test",
                    compatibility=["All nutrient solutions"],
                    warnings=["Caustic - wear gloves", "Use sparingly"]
                )
            ]
        }
    
    def _initialize_schedules(self) -> Dict[GrowType, List[WeeklySchedule]]:
        """Initialize grow schedules for different grow types"""
        schedules = {}
        
        # Autoflower schedule (12 weeks total)
        schedules[GrowType.AUTOFLOWER] = [
            WeeklySchedule(
                week=1,
                phase=GrowPhase.GERMINATION,
                light_schedule="18/6 or 24/0",
                temperature_day="75-80°F",
                temperature_night="70-75°F",
                humidity="70-80%",
                nutrients=[],
                watering_frequency="Mist 2-3 times daily",
                tasks=["Germinate seeds", "Prepare growing medium", "Set up environment"],
                notes="Keep seeds warm and moist. Use paper towel method or direct sow."
            ),
            WeeklySchedule(
                week=2,
                phase=GrowPhase.SEEDLING,
                light_schedule="18/6",
                temperature_day="75-80°F",
                temperature_night="70-75°F",
                humidity="65-70%",
                nutrients=[{"name": "Light feeding", "strength": "1/4", "frequency": "Every 3-4 days"}],
                watering_frequency="Every 2-3 days",
                tasks=["Transplant to small pots", "Begin light feeding", "Monitor for damping off"],
                notes="First true leaves appear. Very gentle with nutrients."
            ),
            WeeklySchedule(
                week=3,
                phase=GrowPhase.VEGETATIVE,
                light_schedule="18/6",
                temperature_day="75-85°F",
                temperature_night="65-75°F",
                humidity="60-65%",
                nutrients=[{"name": "Vegetative nutrients", "strength": "1/2", "frequency": "Every 2-3 days"}],
                watering_frequency="Every 2-3 days",
                tasks=["Increase pot size if needed", "Begin LST if desired", "Monitor growth"],
                notes="Rapid growth begins. Can start gentle training."
            ),
            # Continue with more weeks...
        ]
        
        # Photoperiod from seed schedule (16-20 weeks total)
        schedules[GrowType.PHOTOPERIOD_SEED] = [
            WeeklySchedule(
                week=1,
                phase=GrowPhase.GERMINATION,
                light_schedule="18/6 or 24/0",
                temperature_day="75-80°F",
                temperature_night="70-75°F",
                humidity="70-80%",
                nutrients=[],
                watering_frequency="Mist 2-3 times daily",
                tasks=["Germinate seeds", "Prepare growing medium", "Set up environment"],
                notes="Keep seeds warm and moist. Use paper towel method or direct sow."
            ),
            # Add more weeks for photoperiod...
        ]
        
        return schedules
    
    def get_prerequisites(self, grow_type: GrowType) -> Dict[str, Any]:
        """Get comprehensive prerequisites for a grow type"""
        base_prerequisites = {
            "space_requirements": {
                "minimum_height": "4-6 feet",
                "minimum_area": "2x2 feet for 1 plant",
                "ventilation": "Exhaust fan rated for space volume",
                "electrical": "Dedicated 15-20 amp circuit recommended"
            },
            "legal_requirements": {
                "check_local_laws": "Verify cannabis cultivation laws in your area",
                "plant_limits": "Respect legal plant count limits",
                "privacy": "Ensure grow is not visible to public"
            },
            "basic_knowledge": {
                "plant_biology": "Understanding of cannabis growth phases",
                "environmental_control": "Temperature, humidity, lighting basics",
                "nutrient_management": "NPK ratios and feeding schedules",
                "problem_identification": "Common pests, diseases, deficiencies"
            }
        }
        
        if grow_type == GrowType.AUTOFLOWER:
            base_prerequisites["grow_specific"] = {
                "timeline": "10-12 weeks seed to harvest",
                "light_schedule": "18/6 or 20/4 throughout entire cycle",
                "training": "Gentle LST only, no topping/high stress",
                "nutrients": "Lower nutrient requirements than photoperiod"
            }
        elif grow_type in [GrowType.PHOTOPERIOD_SEED, GrowType.FEMINIZED_SEED]:
            base_prerequisites["grow_specific"] = {
                "timeline": "16-24 weeks seed to harvest",
                "light_schedule": "18/6 veg, 12/12 flower",
                "training": "All training methods suitable",
                "nutrients": "Full strength nutrients in flower"
            }
        
        return base_prerequisites
    
    def get_product_list(self, grow_type: GrowType, budget_level: str = "medium") -> Dict[str, List[Product]]:
        """Get recommended product list based on grow type and budget"""
        budget_filters = {
            "low": lambda p: "$" in p.price_range and not "$200" in p.price_range,
            "medium": lambda p: True,  # Include all products
            "high": lambda p: True  # Include all products, prefer premium
        }
        
        filter_func = budget_filters.get(budget_level, budget_filters["medium"])
        
        filtered_products = {}
        for category, products in self.products.items():
            filtered_products[category] = [p for p in products if filter_func(p)]
        
        return filtered_products
    
    def get_chemical_guide(self, phase: GrowPhase) -> Dict[str, Any]:
        """Get chemical/nutrient guide for specific phase"""
        phase_guides = {
            GrowPhase.GERMINATION: {
                "nutrients_needed": [],
                "supplements": [],
                "ph_range": "6.0-6.5",
                "ec_range": "0.0-0.4",
                "notes": "No nutrients needed, just pH'd water"
            },
            GrowPhase.SEEDLING: {
                "nutrients_needed": ["Light base nutrients"],
                "supplements": ["Cal-Mag if using RO water"],
                "ph_range": "6.0-6.5",
                "ec_range": "0.4-0.8",
                "notes": "Very light feeding, 1/4 strength nutrients"
            },
            GrowPhase.VEGETATIVE: {
                "nutrients_needed": ["Full base nutrients", "Growth enhancers"],
                "supplements": ["Cal-Mag", "Silica", "Enzymes"],
                "ph_range": "6.0-6.5",
                "ec_range": "0.8-1.4",
                "notes": "High nitrogen for vegetative growth"
            },
            GrowPhase.FLOWERING: {
                "nutrients_needed": ["Bloom nutrients", "PK boosters"],
                "supplements": ["Cal-Mag", "Molasses", "Bloom enhancers"],
                "ph_range": "6.0-6.5",
                "ec_range": "1.2-1.8",
                "notes": "Reduce nitrogen, increase phosphorus and potassium"
            }
        }
        
        guide = phase_guides.get(phase, {})
        guide["available_chemicals"] = self.chemicals
        return guide
    
    def get_weekly_schedule(self, grow_type: GrowType, week: int) -> Optional[WeeklySchedule]:
        """Get specific week schedule for grow type"""
        schedules = self.grow_schedules.get(grow_type, [])
        for schedule in schedules:
            if schedule.week == week:
                return schedule
        return None
    
    def create_grow_session(self, strain_name: str, grow_type: GrowType) -> GrowSession:
        """Create new grow tracking session"""
        session = GrowSession(
            id=f"grow_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            strain_name=strain_name,
            grow_type=grow_type,
            start_date=datetime.now(),
            current_week=1,
            current_phase=GrowPhase.GERMINATION,
            expected_harvest=self._calculate_harvest_date(grow_type),
            notes="",
            active=True
        )
        self.active_sessions.append(session)
        return session
    
    def _calculate_harvest_date(self, grow_type: GrowType) -> datetime:
        """Calculate expected harvest date based on grow type"""
        weeks_to_harvest = {
            GrowType.AUTOFLOWER: 12,
            GrowType.PHOTOPERIOD_SEED: 18,
            GrowType.PHOTOPERIOD_CLONE: 14,
            GrowType.FEMINIZED_SEED: 16
        }
        
        weeks = weeks_to_harvest.get(grow_type, 16)
        return datetime.now() + timedelta(weeks=weeks)
    
    def update_session_week(self, session_id: str, new_week: int) -> bool:
        """Update grow session to new week"""
        for session in self.active_sessions:
            if session.id == session_id:
                session.current_week = new_week
                # Update phase based on week and grow type
                session.current_phase = self._determine_phase(session.grow_type, new_week)
                return True
        return False
    
    def _determine_phase(self, grow_type: GrowType, week: int) -> GrowPhase:
        """Determine grow phase based on grow type and week"""
        if grow_type == GrowType.AUTOFLOWER:
            if week <= 1:
                return GrowPhase.GERMINATION
            elif week <= 2:
                return GrowPhase.SEEDLING
            elif week <= 4:
                return GrowPhase.VEGETATIVE
            elif week <= 5:
                return GrowPhase.PRE_FLOWER
            elif week <= 10:
                return GrowPhase.FLOWERING
            elif week <= 11:
                return GrowPhase.HARVEST
            else:
                return GrowPhase.CURING
        else:  # Photoperiod
            if week <= 1:
                return GrowPhase.GERMINATION
            elif week <= 3:
                return GrowPhase.SEEDLING
            elif week <= 10:
                return GrowPhase.VEGETATIVE
            elif week <= 11:
                return GrowPhase.PRE_FLOWER
            elif week <= 18:
                return GrowPhase.FLOWERING
            elif week <= 19:
                return GrowPhase.HARVEST
            else:
                return GrowPhase.CURING
    
    def get_active_sessions(self) -> List[GrowSession]:
        """Get all active grow sessions"""
        return [s for s in self.active_sessions if s.active]
    
    def export_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Export grow session data"""
        for session in self.active_sessions:
            if session.id == session_id:
                return asdict(session)
        return None