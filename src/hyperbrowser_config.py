"""
Hyperbrowser Configuration for GrowWiz Scraper
Optimized settings and target sites for cannabis growing content
"""

from typing import Dict, List, Any

# Hyperbrowser session configurations for different site types
HYPERBROWSER_CONFIGS = {
    "default": {
        "useStealth": True,
        "acceptCookies": True,
        "solveCaptchas": False,
        "useProxy": False
    },
    
    "forums": {
        "useStealth": True,
        "acceptCookies": True,
        "solveCaptchas": True,  # Forums often have captchas
        "useProxy": False
    },
    
    "commercial_sites": {
        "useStealth": True,
        "acceptCookies": True,
        "solveCaptchas": False,
        "useProxy": True  # Commercial sites may block scrapers
    },
    
    "social_media": {
        "useStealth": True,
        "acceptCookies": True,
        "solveCaptchas": True,
        "useProxy": True
    }
}

# Target sites categorized by type and scraping method
TARGET_SITES = {
    "hyperbrowser_priority": {
        # Modern forums requiring JavaScript
        "forums": [
            "https://www.rollitup.org/",
            "https://www.thcfarmer.com/",
            "https://www.autoflower.net/",
            "https://www.icmag.com/",
            "https://www.420magazine.com/",
            "https://www.grasscity.com/",
            "https://www.reddit.com/r/microgrowery/",
            "https://www.reddit.com/r/cannabiscultivation/",
            "https://www.reddit.com/r/SpaceBuckets/"
        ],
        
        # Commercial grow sites
        "commercial": [
            "https://www.leafly.com/news/growing",
            "https://www.growweedeasy.com/",
            "https://www.ilovegrowingmarijuana.com/",
            "https://www.royalqueenseeds.com/blog-n3",
            "https://www.dinafem.org/en/blog/",
            "https://www.barneysfarm.com/blog",
            "https://www.dutch-passion.com/en/blog"
        ],
        
        # YouTube channels (for description scraping)
        "youtube": [
            "https://www.youtube.com/@GrowWeedEasy",
            "https://www.youtube.com/@FromSeedtoStoned",
            "https://www.youtube.com/@MrCanucksGrow",
            "https://www.youtube.com/@BuildASoil",
            "https://www.youtube.com/@KaliConnected"
        ]
    },
    
    "traditional_scraping": {
        # Sites that work well with traditional methods
        "blogs": [
            "https://www.maximumyield.com/",
            "https://www.hightimes.com/grow/",
            "https://www.leafbuyer.com/blog/category/growing/",
            "https://www.cannabisbusinesstimes.com/",
            "https://www.hydroponics.net/"
        ],
        
        # News and article sites
        "news": [
            "https://www.mjbizdaily.com/",
            "https://www.ganjapreneur.com/",
            "https://www.cannabisnow.com/"
        ]
    }
}

# Structured data extraction schemas
EXTRACTION_SCHEMAS = {
    "grow_tips": {
        "type": "object",
        "properties": {
            "grow_tips": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "tip": {"type": "string", "description": "The actual growing tip or advice"},
                        "category": {"type": "string", "description": "Category like nutrients, lighting, watering"},
                        "strain": {"type": "string", "description": "Specific strain if mentioned"},
                        "growth_stage": {"type": "string", "description": "Seedling, vegetative, flowering, harvest"},
                        "difficulty": {"type": "string", "description": "Beginner, intermediate, advanced"},
                        "equipment_needed": {"type": "array", "items": {"type": "string"}},
                        "time_required": {"type": "string", "description": "Time to implement or see results"}
                    },
                    "required": ["tip", "category"]
                }
            }
        }
    },
    
    "problems_solutions": {
        "type": "object",
        "properties": {
            "problems": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "problem": {"type": "string", "description": "Name of the problem"},
                        "symptoms": {
                            "type": "array", 
                            "items": {"type": "string"},
                            "description": "Visual or other symptoms"
                        },
                        "causes": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Possible causes of the problem"
                        },
                        "solutions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Step-by-step solutions"
                        },
                        "severity": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "critical"],
                            "description": "How serious the problem is"
                        },
                        "prevention": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "How to prevent this problem"
                        },
                        "affected_stages": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Which growth stages are affected"
                        }
                    },
                    "required": ["problem", "symptoms", "solutions", "severity"]
                }
            }
        }
    },
    
    "strain_info": {
        "type": "object",
        "properties": {
            "strains": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "type": {"type": "string", "enum": ["indica", "sativa", "hybrid"]},
                        "thc_content": {"type": "string"},
                        "cbd_content": {"type": "string"},
                        "flowering_time": {"type": "string"},
                        "yield": {"type": "string"},
                        "difficulty": {"type": "string", "enum": ["easy", "moderate", "difficult"]},
                        "growing_tips": {"type": "array", "items": {"type": "string"}},
                        "common_problems": {"type": "array", "items": {"type": "string"}},
                        "ideal_conditions": {
                            "type": "object",
                            "properties": {
                                "temperature": {"type": "string"},
                                "humidity": {"type": "string"},
                                "ph": {"type": "string"},
                                "nutrients": {"type": "array", "items": {"type": "string"}}
                            }
                        }
                    },
                    "required": ["name", "type"]
                }
            }
        }
    },
    
    "equipment_reviews": {
        "type": "object",
        "properties": {
            "equipment": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "category": {"type": "string", "description": "lights, nutrients, tents, etc."},
                        "rating": {"type": "number", "minimum": 0, "maximum": 10},
                        "pros": {"type": "array", "items": {"type": "string"}},
                        "cons": {"type": "array", "items": {"type": "string"}},
                        "price_range": {"type": "string"},
                        "best_for": {"type": "string", "description": "What type of grower this is best for"},
                        "alternatives": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["name", "category", "rating"]
                }
            }
        }
    }
}

# Extraction prompts for different content types
EXTRACTION_PROMPTS = {
    "grow_tips": """
    Extract practical cannabis growing tips from this content. Focus on:
    - Specific, actionable advice
    - Techniques for improving yield or quality
    - Problem prevention methods
    - Equipment recommendations
    - Timing and scheduling advice
    
    Categorize tips by: nutrients, lighting, watering, training, harvesting, curing, etc.
    Include growth stage information when available.
    """,
    
    "problems_solutions": """
    Extract cannabis plant problems and their solutions from this content. Focus on:
    - Clear problem identification
    - Visual symptoms and signs
    - Root causes and contributing factors
    - Step-by-step solutions
    - Prevention strategies
    
    Rate severity as: low (cosmetic), medium (affects growth), high (threatens plant), critical (plant death risk)
    """,
    
    "strain_info": """
    Extract cannabis strain information from this content. Focus on:
    - Strain names and genetics
    - Growth characteristics
    - Flowering times and yields
    - Difficulty levels for growing
    - Specific growing requirements
    - Common issues with each strain
    """,
    
    "equipment_reviews": """
    Extract cannabis growing equipment reviews and recommendations. Focus on:
    - Product names and categories
    - Performance ratings and reviews
    - Pros and cons from user experience
    - Price points and value assessments
    - Comparisons with alternatives
    - Suitability for different grow setups
    """
}

# Rate limiting and crawling settings
CRAWLING_SETTINGS = {
    "max_pages_per_site": 25,
    "delay_between_requests": 2.0,
    "max_concurrent_requests": 3,
    "timeout_seconds": 30,
    "retry_attempts": 2,
    "respect_robots_txt": True
}

# Content filtering and relevance settings
CONTENT_FILTERS = {
    "min_content_length": 100,
    "max_content_length": 2000,
    "relevance_threshold": 0.3,
    "duplicate_similarity_threshold": 0.8,
    
    "required_keywords": [
        "cannabis", "marijuana", "grow", "plant", "cultivation",
        "nutrient", "light", "water", "soil", "hydro"
    ],
    
    "bonus_keywords": [
        "deficiency", "problem", "solution", "tip", "advice",
        "flowering", "vegetative", "harvest", "yield", "strain"
    ],
    
    "exclude_keywords": [
        "legal", "law", "arrest", "illegal", "drug test",
        "medical prescription", "dispensary hours"
    ]
}

def get_hyperbrowser_config(site_type: str = "default") -> Dict[str, Any]:
    """Get Hyperbrowser configuration for specific site type"""
    return HYPERBROWSER_CONFIGS.get(site_type, HYPERBROWSER_CONFIGS["default"])

def get_extraction_schema(schema_type: str) -> Dict[str, Any]:
    """Get extraction schema for specific content type"""
    return EXTRACTION_SCHEMAS.get(schema_type, EXTRACTION_SCHEMAS["grow_tips"])

def get_extraction_prompt(prompt_type: str) -> str:
    """Get extraction prompt for specific content type"""
    return EXTRACTION_PROMPTS.get(prompt_type, EXTRACTION_PROMPTS["grow_tips"])

def get_target_sites(method: str = "hyperbrowser_priority") -> Dict[str, List[str]]:
    """Get target sites for specific scraping method"""
    return TARGET_SITES.get(method, TARGET_SITES["hyperbrowser_priority"])

def is_content_relevant(content: str) -> bool:
    """Check if content meets relevance criteria"""
    content_lower = content.lower()
    
    # Check length
    if len(content) < CONTENT_FILTERS["min_content_length"]:
        return False
    
    if len(content) > CONTENT_FILTERS["max_content_length"]:
        return False
    
    # Check for required keywords
    required_found = any(keyword in content_lower for keyword in CONTENT_FILTERS["required_keywords"])
    if not required_found:
        return False
    
    # Check for excluded keywords
    excluded_found = any(keyword in content_lower for keyword in CONTENT_FILTERS["exclude_keywords"])
    if excluded_found:
        return False
    
    return True

def calculate_content_score(content: str) -> float:
    """Calculate relevance score for content"""
    content_lower = content.lower()
    score = 0.0
    
    # Base score for required keywords
    required_matches = sum(1 for keyword in CONTENT_FILTERS["required_keywords"] if keyword in content_lower)
    score += required_matches * 0.2
    
    # Bonus for bonus keywords
    bonus_matches = sum(1 for keyword in CONTENT_FILTERS["bonus_keywords"] if keyword in content_lower)
    score += bonus_matches * 0.1
    
    # Length bonus
    if CONTENT_FILTERS["min_content_length"] < len(content) < CONTENT_FILTERS["max_content_length"]:
        score += 0.1
    
    return min(score, 1.0)  # Cap at 1.0