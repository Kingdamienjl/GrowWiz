"""
Advanced Care Sheet Generator for Cannabis Strains
Generates detailed, individualized growing guides based on strain characteristics
"""

import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@dataclass
class GrowingPhase:
    """Represents a specific growing phase with detailed instructions"""
    name: str
    duration: str
    light_schedule: str
    temperature_day: str
    temperature_night: str
    humidity: str
    nutrients: List[str]
    watering_frequency: str
    special_notes: List[str]

class AdvancedCareSheetGenerator:
    """Generates detailed, strain-specific care sheets"""
    
    def __init__(self):
        self.strain_specific_tips = {
            "indica": {
                "structure": "Bushy, compact growth pattern",
                "training": "LST (Low Stress Training) works well due to shorter stature",
                "flowering": "Generally shorter flowering period, watch for dense buds",
                "harvest_timing": "Harvest when trichomes are mostly amber for sedative effects"
            },
            "sativa": {
                "structure": "Tall, stretchy growth pattern",
                "training": "SCROG (Screen of Green) recommended to manage height",
                "flowering": "Longer flowering period, requires patience",
                "harvest_timing": "Harvest when trichomes are milky for energetic effects"
            },
            "hybrid": {
                "structure": "Balanced growth characteristics",
                "training": "Various training methods work well",
                "flowering": "Moderate flowering period",
                "harvest_timing": "Harvest timing depends on desired effects"
            }
        }
        
        self.difficulty_adjustments = {
            "Easy": {
                "nutrient_strength": "Start with 1/4 strength nutrients",
                "monitoring": "Check plants every 2-3 days",
                "forgiveness": "Tolerates minor mistakes well"
            },
            "Moderate": {
                "nutrient_strength": "Start with 1/2 strength nutrients",
                "monitoring": "Check plants daily",
                "forgiveness": "Requires consistent care"
            },
            "Difficult": {
                "nutrient_strength": "Precise nutrient management required",
                "monitoring": "Check plants twice daily",
                "forgiveness": "Very sensitive to environmental changes"
            }
        }
    
    def generate_comprehensive_care_sheet(self, strain_data: Dict[str, Any]) -> str:
        """Generate a comprehensive, individualized care sheet"""
        name = strain_data.get('name', 'Unknown')
        strain_type = strain_data.get('strain_type', 'Unknown').lower()
        difficulty = strain_data.get('growing_difficulty', 'Moderate')
        
        # Generate growing phases
        phases = self._generate_growing_phases(strain_data)
        
        # Generate strain-specific recommendations
        recommendations = self._generate_strain_recommendations(strain_data)
        
        # Generate timeline
        timeline = self._generate_growing_timeline(strain_data)
        
        # Generate troubleshooting guide
        troubleshooting = self._generate_troubleshooting_guide(strain_data)
        
        care_sheet = f"""# 🌿 {name} - Complete Growing Care Sheet

## Strain Profile
- **Type**: {strain_data.get('strain_type', 'Unknown').title()}
- **Difficulty**: {difficulty}
- **Genetics**: {strain_data.get('genetics', 'Unknown')}
- **Flowering Time**: {strain_data.get('flowering_time', 'Unknown')}
- **Expected Yield**: {strain_data.get('yield_info', 'Unknown')}
- **Height**: {strain_data.get('height', 'Unknown')}
- **Climate**: {strain_data.get('climate', 'Unknown')}

## Growing Phases

{self._format_growing_phases(phases)}

## Strain-Specific Recommendations

{recommendations}

## Growing Timeline

{timeline}

## Nutrient Schedule

{self._generate_nutrient_schedule(strain_data)}

## Environmental Controls

{self._generate_environmental_guide(strain_data)}

## Training Techniques

{self._generate_training_guide(strain_data)}

## Harvest & Curing Guide

{self._generate_harvest_guide(strain_data)}

## Troubleshooting

{troubleshooting}

## Expected Results
- **Effects**: {', '.join(strain_data.get('effects', []))}
- **Medical Uses**: {', '.join(strain_data.get('medical_uses', []))}
- **Flavors**: {', '.join(strain_data.get('flavors', []))}
- **Aromas**: {', '.join(strain_data.get('aromas', []))}

---
*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*This care sheet is tailored specifically for {name} based on its genetic profile and characteristics.*
"""
        return care_sheet
    
    def _generate_growing_phases(self, strain_data: Dict[str, Any]) -> List[GrowingPhase]:
        """Generate detailed growing phases for the strain"""
        strain_type = strain_data.get('strain_type', 'Unknown').lower()
        difficulty = strain_data.get('growing_difficulty', 'Moderate')
        
        phases = []
        
        # Seedling Phase
        phases.append(GrowingPhase(
            name="Seedling",
            duration="1-2 weeks",
            light_schedule="18/6 or 24/0",
            temperature_day="75-80°F (24-27°C)",
            temperature_night="70-75°F (21-24°C)",
            humidity="65-70%",
            nutrients=["Very light nutrients", "Root stimulator", "Cal-Mag if needed"],
            watering_frequency="Every 2-3 days, keep soil moist but not wet",
            special_notes=[
                "Use gentle lighting (T5 or low-power LED)",
                "Maintain consistent moisture",
                "Watch for damping off"
            ]
        ))
        
        # Vegetative Phase
        veg_duration = "4-6 weeks" if strain_type == "indica" else "6-8 weeks" if strain_type == "sativa" else "4-8 weeks"
        phases.append(GrowingPhase(
            name="Vegetative",
            duration=veg_duration,
            light_schedule="18/6",
            temperature_day="75-85°F (24-29°C)",
            temperature_night="65-75°F (18-24°C)",
            humidity="55-65%",
            nutrients=["High nitrogen nutrients", "Growth enhancers", "Cal-Mag supplement"],
            watering_frequency="Every 2-3 days, water when top inch of soil is dry",
            special_notes=[
                f"Ideal for {self.strain_specific_tips.get(strain_type, {}).get('training', 'various training methods')}",
                "Increase nutrients gradually",
                "Monitor for nutrient deficiencies"
            ]
        ))
        
        # Pre-flowering Phase
        phases.append(GrowingPhase(
            name="Pre-flowering",
            duration="1-2 weeks",
            light_schedule="12/12",
            temperature_day="75-80°F (24-27°C)",
            temperature_night="65-70°F (18-21°C)",
            humidity="50-55%",
            nutrients=["Transition nutrients", "Reduced nitrogen", "Increased phosphorus"],
            watering_frequency="Every 2-3 days, monitor closely for changes",
            special_notes=[
                "Watch for sex determination",
                "Remove male plants if growing from regular seeds",
                "Begin defoliation if needed"
            ]
        ))
        
        # Flowering Phase
        flowering_time = strain_data.get('flowering_time', '8-10 weeks')
        phases.append(GrowingPhase(
            name="Flowering",
            duration=flowering_time,
            light_schedule="12/12",
            temperature_day="70-80°F (21-27°C)",
            temperature_night="60-70°F (15-21°C)",
            humidity="40-50%",
            nutrients=["Bloom nutrients", "High phosphorus/potassium", "Bloom boosters"],
            watering_frequency="Every 2-4 days, reduce frequency as harvest approaches",
            special_notes=[
                f"Expect {self.strain_specific_tips.get(strain_type, {}).get('flowering', 'typical flowering behavior')}",
                "Monitor trichomes for harvest timing",
                "Reduce humidity to prevent mold"
            ]
        ))
        
        return phases
    
    def _format_growing_phases(self, phases: List[GrowingPhase]) -> str:
        """Format growing phases into readable text"""
        formatted = ""
        for phase in phases:
            formatted += f"""
### {phase.name} Phase ({phase.duration})

**Environmental Settings:**
- Light Schedule: {phase.light_schedule}
- Day Temperature: {phase.temperature_day}
- Night Temperature: {phase.temperature_night}
- Humidity: {phase.humidity}

**Nutrition:**
{chr(10).join([f"- {nutrient}" for nutrient in phase.nutrients])}

**Watering:**
- {phase.watering_frequency}

**Special Notes:**
{chr(10).join([f"- {note}" for note in phase.special_notes])}

"""
        return formatted
    
    def _generate_strain_recommendations(self, strain_data: Dict[str, Any]) -> str:
        """Generate strain-specific growing recommendations"""
        strain_type = strain_data.get('strain_type', 'Unknown').lower()
        difficulty = strain_data.get('growing_difficulty', 'Moderate')
        height = strain_data.get('height', 'Unknown')
        
        tips = self.strain_specific_tips.get(strain_type, {})
        difficulty_info = self.difficulty_adjustments.get(difficulty, {})
        
        recommendations = f"""
### Strain Type Characteristics ({strain_type.title()})
- **Growth Pattern**: {tips.get('structure', 'Standard growth pattern')}
- **Training Recommendation**: {tips.get('training', 'Standard training methods')}
- **Flowering Notes**: {tips.get('flowering', 'Standard flowering period')}
- **Harvest Timing**: {tips.get('harvest_timing', 'Standard harvest timing')}

### Difficulty Level ({difficulty})
- **Nutrient Approach**: {difficulty_info.get('nutrient_strength', 'Standard nutrient approach')}
- **Monitoring**: {difficulty_info.get('monitoring', 'Regular monitoring')}
- **Tolerance**: {difficulty_info.get('forgiveness', 'Standard tolerance')}

### Height Management
- **Expected Height**: {height}
- **Space Requirements**: {"Requires vertical space management" if "tall" in height.lower() or "180" in height else "Compact growth, suitable for smaller spaces"}
"""
        return recommendations
    
    def _generate_growing_timeline(self, strain_data: Dict[str, Any]) -> str:
        """Generate a week-by-week growing timeline"""
        flowering_time = strain_data.get('flowering_time', '8-10 weeks')
        
        # Extract numeric weeks from flowering time
        import re
        weeks_match = re.search(r'(\d+)', flowering_time)
        flowering_weeks = int(weeks_match.group(1)) if weeks_match else 8
        
        total_weeks = 2 + 6 + flowering_weeks  # seedling + veg + flowering
        
        timeline = f"""
### Complete Growing Timeline ({total_weeks} weeks total)

**Weeks 1-2: Seedling Stage**
- Week 1: Germination and first true leaves
- Week 2: Establish root system, gentle feeding

**Weeks 3-8: Vegetative Stage**
- Week 3-4: Rapid growth begins, increase nutrients
- Week 5-6: Training and shaping, full feeding
- Week 7-8: Pre-flower preparation, transition nutrients

**Weeks 9-{8 + flowering_weeks}: Flowering Stage**
- Week 9-10: Flower initiation, bloom nutrients
- Week {11}-{6 + flowering_weeks}: Bud development, maintain environment
- Week {7 + flowering_weeks}-{8 + flowering_weeks}: Final ripening, flush nutrients

**Harvest Window**: Week {8 + flowering_weeks} (monitor trichomes)
"""
        return timeline
    
    def _generate_nutrient_schedule(self, strain_data: Dict[str, Any]) -> str:
        """Generate detailed nutrient schedule"""
        difficulty = strain_data.get('growing_difficulty', 'Moderate')
        
        base_strength = {
            "Easy": "1/4 to 1/2 strength",
            "Moderate": "1/2 to 3/4 strength", 
            "Difficult": "3/4 to full strength"
        }.get(difficulty, "1/2 to 3/4 strength")
        
        schedule = f"""
### Nutrient Schedule (Base strength: {base_strength})

**Seedling (Weeks 1-2):**
- EC: 0.4-0.6 | pH: 6.0-6.5
- Light feeding with root stimulator
- Cal-Mag: 1ml/L if needed

**Vegetative (Weeks 3-8):**
- EC: 0.8-1.4 | pH: 6.0-6.5
- High nitrogen base nutrients
- Growth enhancers and enzymes
- Cal-Mag: 2-3ml/L

**Pre-flowering (Week 9):**
- EC: 1.0-1.6 | pH: 6.0-6.5
- Transition to bloom nutrients
- Reduce nitrogen gradually

**Flowering (Weeks 10+):**
- EC: 1.2-1.8 | pH: 6.0-6.5
- Bloom base nutrients
- PK boosters in mid-flower
- Flush last 1-2 weeks

**Important Notes:**
- Start at lower EC values and increase gradually
- Monitor plant response and adjust accordingly
- Always pH test your nutrient solution
"""
        return schedule
    
    def _generate_environmental_guide(self, strain_data: Dict[str, Any]) -> str:
        """Generate environmental control guide"""
        climate = strain_data.get('climate', 'Unknown')
        
        guide = f"""
### Environmental Control Guide

**Climate Preference**: {climate}

**Temperature Management:**
- Vegetative: 75-85°F day, 65-75°F night
- Flowering: 70-80°F day, 60-70°F night
- Avoid temperature swings >10°F

**Humidity Control:**
- Seedling: 65-70%
- Vegetative: 55-65%
- Flowering: 40-50%
- Late flowering: 35-45%

**Air Circulation:**
- Gentle breeze on plants at all times
- Exhaust fan for heat and humidity control
- Fresh air intake for CO2 replenishment

**Lighting:**
- Vegetative: 400-600 PPFD
- Flowering: 600-900 PPFD
- 18/6 schedule for veg, 12/12 for flower
- Maintain proper light distance to prevent burn
"""
        return guide
    
    def _generate_training_guide(self, strain_data: Dict[str, Any]) -> str:
        """Generate training technique guide"""
        strain_type = strain_data.get('strain_type', 'Unknown').lower()
        height = strain_data.get('height', 'Unknown')
        
        training_rec = self.strain_specific_tips.get(strain_type, {}).get('training', 'various training methods')
        
        guide = f"""
### Training Techniques

**Recommended for this strain**: {training_rec}

**Low Stress Training (LST):**
- Best for: All strain types, especially indica
- When: Start in early vegetative stage
- Method: Gently bend and tie down branches

**Screen of Green (SCROG):**
- Best for: Sativa and tall-growing strains
- When: 2-3 weeks into vegetative
- Method: Use screen to control canopy height

**Topping/FIMing:**
- Best for: Vigorous growers
- When: After 4-6 nodes develop
- Method: Cut main stem to encourage branching

**Defoliation:**
- Best for: Dense, bushy strains
- When: Early flower and week 3 of flower
- Method: Remove fan leaves blocking bud sites

**Height Considerations:**
- Expected height: {height}
- {"Use height control techniques" if "tall" in height.lower() or (re.search(r'(\d+)', height) and int(re.search(r'(\d+)', height).group(1)) > 120) else "Compact growth, minimal training needed"}
"""
        return guide
    
    def _generate_harvest_guide(self, strain_data: Dict[str, Any]) -> str:
        """Generate harvest and curing guide"""
        strain_type = strain_data.get('strain_type', 'Unknown').lower()
        effects = strain_data.get('effects', [])
        
        harvest_timing = self.strain_specific_tips.get(strain_type, {}).get('harvest_timing', 'Standard harvest timing')
        
        guide = f"""
### Harvest & Curing Guide

**Harvest Timing**: {harvest_timing}

**Trichome Inspection:**
- Clear: Too early, low potency
- Milky/Cloudy: Peak THC, energetic effects
- Amber: CBN conversion, sedative effects
- Target: 70-80% milky, 20-30% amber for balanced effects

**Harvest Process:**
1. Stop feeding 1-2 weeks before harvest
2. Check trichomes with jeweler's loupe
3. Harvest in morning after lights on
4. Cut branches and hang in dark, ventilated area

**Drying (7-14 days):**
- Temperature: 60-70°F
- Humidity: 45-55%
- Dark environment with air circulation
- Stems should snap, not bend when ready

**Curing (2-8 weeks):**
- Store in airtight jars at 62% humidity
- Open jars daily for first week (burping)
- Gradually reduce to weekly opening
- Optimal cure: 4-6 weeks minimum

**Expected Results:**
- Effects: {', '.join(effects)}
- Flavor development improves with longer cure
- Potency stabilizes after 2-4 weeks
"""
        return guide
    
    def _generate_troubleshooting_guide(self, strain_data: Dict[str, Any]) -> str:
        """Generate troubleshooting guide"""
        difficulty = strain_data.get('growing_difficulty', 'Moderate')
        strain_type = strain_data.get('strain_type', 'Unknown').lower()
        
        guide = f"""
### Troubleshooting Guide

**Common Issues for {difficulty} Strains:**

**Nutrient Problems:**
- Yellowing leaves: Nitrogen deficiency (veg) or natural senescence (flower)
- Brown leaf tips: Nutrient burn, reduce feeding
- Purple stems: Phosphorus deficiency or genetics
- Interveinal chlorosis: Iron or magnesium deficiency

**Environmental Issues:**
- Stretching: Insufficient light or too much heat
- Slow growth: Low temperatures or overwatering
- Leaf curl: Heat stress or wind burn
- Mold/mildew: High humidity, poor air circulation

**Strain-Specific Considerations:**
{f"- Indica strains: Watch for dense bud mold in late flower" if strain_type == "indica" else ""}
{f"- Sativa strains: May need height control, longer flowering" if strain_type == "sativa" else ""}
{f"- Hybrid strains: Monitor for mixed characteristics" if strain_type == "hybrid" else ""}

**Emergency Actions:**
- Overwatering: Stop watering, improve drainage
- Heat stress: Increase ventilation, raise lights
- Nutrient lockout: Flush with pH'd water
- Pest issues: Identify and treat immediately

**When to Seek Help:**
- Rapid plant decline
- Unknown pest identification
- Persistent nutrient issues
- Environmental control problems
"""
        return guide
    
    def generate_quick_reference_card(self, strain_data: Dict[str, Any]) -> str:
        """Generate a quick reference card for the strain"""
        name = strain_data.get('name', 'Unknown')
        
        card = f"""
# {name} - Quick Reference Card

## Key Stats
- **Type**: {strain_data.get('strain_type', 'Unknown').title()}
- **Difficulty**: {strain_data.get('growing_difficulty', 'Unknown')}
- **Flowering**: {strain_data.get('flowering_time', 'Unknown')}
- **Height**: {strain_data.get('height', 'Unknown')}
- **Yield**: {strain_data.get('yield_info', 'Unknown')}

## Critical Points
- **Best Training**: {self.strain_specific_tips.get(strain_data.get('strain_type', '').lower(), {}).get('training', 'Standard methods')}
- **Harvest Window**: {self.strain_specific_tips.get(strain_data.get('strain_type', '').lower(), {}).get('harvest_timing', 'Standard timing')}
- **Watch For**: {"Dense bud mold" if strain_data.get('strain_type', '').lower() == 'indica' else "Height management" if strain_data.get('strain_type', '').lower() == 'sativa' else "Balanced characteristics"}

## Emergency Contacts
- pH Range: 6.0-6.5 (soil), 5.5-6.5 (hydro)
- EC Range: 0.8-1.8 (depending on stage)
- Temperature: 70-80°F day, 60-70°F night
- Humidity: 40-60% (stage dependent)

---
*Keep this card handy during your grow!*
"""
        return card

if __name__ == "__main__":
    # Test the care sheet generator
    test_strain = {
        "name": "Blue Dream",
        "strain_type": "hybrid",
        "thc_content": "17-24%",
        "cbd_content": "0.1-0.2%",
        "genetics": "Blueberry × Haze",
        "flowering_time": "9-10 weeks",
        "yield_info": "500-600g/m²",
        "effects": ["euphoric", "relaxed", "happy", "creative"],
        "medical_uses": ["stress", "depression", "pain", "fatigue"],
        "flavors": ["berry", "sweet", "vanilla"],
        "aromas": ["blueberry", "sweet", "herbal"],
        "growing_difficulty": "Easy",
        "height": "120-180cm",
        "climate": "Indoor/Outdoor",
        "description": "Blue Dream is a popular sativa-dominant hybrid strain."
    }
    
    generator = AdvancedCareSheetGenerator()
    care_sheet = generator.generate_comprehensive_care_sheet(test_strain)
    print(care_sheet)