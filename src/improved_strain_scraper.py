#!/usr/bin/env python3
"""
Improved Strain Scraper for GrowWiz
Addresses data quality issues:
- Extracts THC/CBD percentages from descriptions
- Cleans strain names (removes "Marijuana Strain" suffix)
- Adds strain bud images
- Improved Google Drive backup
"""

import asyncio
import json
import logging
import re
import random
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
import requests
from bs4 import BeautifulSoup
import time

# Import existing modules
from gdrive_manager import GDriveStrainManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ImprovedStrainData:
    """Enhanced data structure for marijuana strain information with improved data quality"""
    name: str
    strain_type: Optional[str] = None
    thc_content: Optional[str] = None
    cbd_content: Optional[str] = None
    genetics: Optional[str] = None
    flowering_time: Optional[str] = None
    yield_info: Optional[str] = None
    effects: List[str] = None
    medical_uses: List[str] = None
    flavors: List[str] = None
    aromas: List[str] = None
    growing_difficulty: Optional[str] = None
    height: Optional[str] = None
    climate: Optional[str] = None
    description: Optional[str] = None
    breeder: Optional[str] = None
    awards: List[str] = None
    source_url: Optional[str] = None
    scraped_at: Optional[str] = None
    popularity_score: Optional[int] = None
    price_range: Optional[str] = None
    seed_availability: Optional[str] = None
    grow_tips: List[str] = None
    harvest_weight: Optional[str] = None
    flowering_type: Optional[str] = None
    resistance: List[str] = None
    terpenes: List[str] = None
    lineage: Optional[str] = None
    image_url: Optional[str] = None  # New field for strain bud images
    
    def __post_init__(self):
        # Initialize lists if None
        if self.effects is None:
            self.effects = []
        if self.medical_uses is None:
            self.medical_uses = []
        if self.flavors is None:
            self.flavors = []
        if self.aromas is None:
            self.aromas = []
        if self.awards is None:
            self.awards = []
        if self.grow_tips is None:
            self.grow_tips = []
        if self.resistance is None:
            self.resistance = []
        if self.terpenes is None:
            self.terpenes = []

class ImprovedStrainScraper:
    """Improved strain scraper with enhanced data quality and image support"""
    
    def __init__(self):
        self.scraped_strains = []
        self.gdrive_manager = GDriveStrainManager()
        
        # Enhanced THC/CBD extraction patterns
        self.thc_patterns = [
            r'THC[:\s]*(\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?)%',
            r'thc[:\s]*(\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?)%',
            r'(\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?)%\s*THC',
            r'(\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?)%\s*thc',
        ]
        
        self.cbd_patterns = [
            r'CBD[:\s]*(\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?)%',
            r'cbd[:\s]*(\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?)%',
            r'(\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?)%\s*CBD',
            r'(\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?)%\s*cbd',
        ]
        
        # Image search patterns for strain buds
        self.image_selectors = [
            'img[alt*="strain"]',
            'img[alt*="bud"]',
            'img[alt*="cannabis"]',
            'img[alt*="marijuana"]',
            '.strain-image img',
            '.bud-image img',
            '.product-image img',
            '.strain-photo img'
        ]
        
        # Strain name cleanup patterns
        self.name_cleanup_patterns = [
            r'\s+Marijuana\s+Strain$',
            r'\s+Cannabis\s+Strain$',
            r'\s+Weed\s+Strain$',
            r'\s+Strain$',
            r'^\s*Find\s+the\s+perfect\s+strain.*',
            r'.*with\s+Information.*Reviews.*'
        ]
        
    def clean_strain_name(self, name: str) -> str:
        """Clean strain name by removing redundant suffixes"""
        if not name or not isinstance(name, str):
            return ""
            
        cleaned_name = name.strip()
        
        # Apply cleanup patterns
        for pattern in self.name_cleanup_patterns:
            cleaned_name = re.sub(pattern, '', cleaned_name, flags=re.IGNORECASE)
        
        # Remove extra whitespace
        cleaned_name = re.sub(r'\s+', ' ', cleaned_name).strip()
        
        # Skip invalid names
        if len(cleaned_name) < 2 or cleaned_name.lower() in ['find', 'strain', 'cannabis', 'marijuana']:
            return ""
            
        return cleaned_name
    
    def extract_thc_from_description(self, description: str) -> Optional[str]:
        """Extract THC percentage from description text"""
        if not description:
            return None
            
        for pattern in self.thc_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                thc_value = match.group(1).strip()
                # Validate the extracted value
                if re.match(r'^\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?$', thc_value):
                    return f"{thc_value}%"
        
        return None
    
    def extract_cbd_from_description(self, description: str) -> Optional[str]:
        """Extract CBD percentage from description text"""
        if not description:
            return None
            
        for pattern in self.cbd_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                cbd_value = match.group(1).strip()
                # Validate the extracted value
                if re.match(r'^\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?$', cbd_value):
                    return f"{cbd_value}%"
        
        return None
    
    def extract_strain_image(self, soup: BeautifulSoup, strain_name: str) -> Optional[str]:
        """Extract strain bud image URL"""
        try:
            # Try multiple image selectors
            for selector in self.image_selectors:
                images = soup.select(selector)
                for img in images:
                    src = img.get('src') or img.get('data-src')
                    if src and self.is_valid_strain_image(src, strain_name):
                        # Convert relative URLs to absolute
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif src.startswith('/'):
                            # Would need base URL - skip for now
                            continue
                        return src
            
            # Fallback: look for any cannabis-related images
            all_images = soup.find_all('img')
            for img in all_images:
                src = img.get('src') or img.get('data-src')
                alt = img.get('alt', '').lower()
                if src and any(keyword in alt for keyword in ['cannabis', 'marijuana', 'bud', 'strain']):
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif not src.startswith('http'):
                        continue
                    return src
                    
        except Exception as e:
            logger.debug(f"Error extracting image: {e}")
        
        return None
    
    def is_valid_strain_image(self, src: str, strain_name: str) -> bool:
        """Check if image URL is likely a strain bud image"""
        if not src:
            return False
            
        src_lower = src.lower()
        name_lower = strain_name.lower()
        
        # Check for strain-specific images
        if any(word in src_lower for word in name_lower.split()):
            return True
            
        # Check for cannabis-related keywords in URL
        cannabis_keywords = ['strain', 'bud', 'cannabis', 'marijuana', 'weed', 'flower']
        if any(keyword in src_lower for keyword in cannabis_keywords):
            return True
            
        # Avoid logos, icons, and ads
        avoid_keywords = ['logo', 'icon', 'ad', 'banner', 'header', 'footer', 'nav']
        if any(keyword in src_lower for keyword in avoid_keywords):
            return False
            
        return False
    
    async def improve_existing_data(self, input_file: str, output_file: str) -> Dict[str, Any]:
        """Improve existing strain data by extracting missing THC/CBD and cleaning names"""
        logger.info(f"Improving existing strain data from {input_file}")
        
        try:
            # Load existing data
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            improved_strains = []
            improvements_made = {
                'names_cleaned': 0,
                'thc_extracted': 0,
                'cbd_extracted': 0,
                'invalid_strains_removed': 0,
                'images_added': 0
            }
            
            strains = data.get('strains', [])
            logger.info(f"Processing {len(strains)} strains for improvement...")
            
            for i, strain_data in enumerate(strains):
                if i % 25 == 0:
                    logger.info(f"Processing strain {i+1}/{len(strains)}")
                
                # Clean strain name
                original_name = strain_data.get('name', '')
                cleaned_name = self.clean_strain_name(original_name)
                
                # Skip invalid strains
                if not cleaned_name or original_name in ['Find the perfect strain for you.', 'Indica Marijuana Strains with Information, Photos & Reviews']:
                    logger.debug(f"Skipping invalid entry: {original_name}")
                    improvements_made['invalid_strains_removed'] += 1
                    continue
                
                if cleaned_name != original_name:
                    improvements_made['names_cleaned'] += 1
                
                # Extract THC/CBD from description if missing
                description = strain_data.get('description', '') or ''
                thc_content = strain_data.get('thc_content')
                cbd_content = strain_data.get('cbd_content')
                
                if not thc_content and description:
                    extracted_thc = self.extract_thc_from_description(description)
                    if extracted_thc:
                        thc_content = extracted_thc
                        improvements_made['thc_extracted'] += 1
                
                if not cbd_content and description:
                    extracted_cbd = self.extract_cbd_from_description(description)
                    if extracted_cbd:
                        cbd_content = extracted_cbd
                        improvements_made['cbd_extracted'] += 1
                
                logger.debug(f"Strain: {cleaned_name} | THC: {thc_content} | CBD: {cbd_content}")
                
                # Try to add image if missing
                image_url = strain_data.get('image_url')
                if not image_url:
                    # Try to fetch image from source URL
                    source_url = strain_data.get('source_url')
                    if source_url:
                        try:
                            image_url = await self.fetch_strain_image(source_url, cleaned_name)
                            if image_url:
                                improvements_made['images_added'] += 1
                        except:
                            pass
                
                # Create improved strain data
                improved_strain = ImprovedStrainData(
                    name=cleaned_name,
                    strain_type=strain_data.get('strain_type'),
                    thc_content=thc_content,
                    cbd_content=cbd_content,
                    genetics=strain_data.get('genetics'),
                    flowering_time=strain_data.get('flowering_time'),
                    yield_info=strain_data.get('yield_info'),
                    effects=strain_data.get('effects', []),
                    medical_uses=strain_data.get('medical_uses', []),
                    flavors=strain_data.get('flavors', []),
                    aromas=strain_data.get('aromas', []),
                    growing_difficulty=strain_data.get('growing_difficulty'),
                    height=strain_data.get('height'),
                    climate=strain_data.get('climate'),
                    description=description,
                    breeder=strain_data.get('breeder'),
                    awards=strain_data.get('awards', []),
                    source_url=strain_data.get('source_url'),
                    scraped_at=strain_data.get('scraped_at'),
                    popularity_score=strain_data.get('popularity_score'),
                    price_range=strain_data.get('price_range'),
                    seed_availability=strain_data.get('seed_availability'),
                    grow_tips=strain_data.get('grow_tips', []),
                    harvest_weight=strain_data.get('harvest_weight'),
                    flowering_type=strain_data.get('flowering_type'),
                    resistance=strain_data.get('resistance', []),
                    terpenes=strain_data.get('terpenes', []),
                    lineage=strain_data.get('lineage'),
                    image_url=image_url
                )
                
                improved_strains.append(improved_strain)
            
            # Save improved data
            improved_data = {
                'scraped_at': datetime.now().isoformat(),
                'total_strains': len(improved_strains),
                'improvements_made': improvements_made,
                'strains': [asdict(strain) for strain in improved_strains]
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(improved_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Improved data saved to {output_file}")
            logger.info(f"Improvements: {improvements_made}")
            
            return improved_data
            
        except Exception as e:
            logger.error(f"Error improving strain data: {e}")
            return {}
    
    async def fetch_strain_image(self, url: str, strain_name: str) -> Optional[str]:
        """Fetch strain image from source URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                return self.extract_strain_image(soup, strain_name)
                
        except Exception as e:
            logger.debug(f"Error fetching image from {url}: {e}")
        
        return None
    
    async def backup_to_gdrive(self, data_file: str) -> bool:
        """Backup improved strain data to Google Drive"""
        try:
            logger.info("Backing up improved strain data to Google Drive...")
            
            # Load the improved data
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            strains_data = data.get('strains', [])
            
            # Use the organize_strains_to_drive method
            result = await self.gdrive_manager.organize_strains_to_drive(strains_data)
            
            if result.get('success', False):
                logger.info("✅ Strain data successfully backed up to Google Drive")
                logger.info(f"Uploaded {result.get('uploaded_strains', 0)} strains")
                return True
            else:
                logger.error("❌ Failed to backup strain data to Google Drive")
                logger.error(f"Errors: {result.get('errors', [])}")
                return False
                
        except Exception as e:
            logger.error(f"Error backing up to Google Drive: {e}")
            return False
    
    def generate_summary_report(self, improved_data: Dict[str, Any]) -> str:
        """Generate a summary report of improvements made"""
        improvements = improved_data.get('improvements_made', {})
        total_strains = improved_data.get('total_strains', 0)
        
        report = f"""
🌿 GROWWIZ STRAIN DATA IMPROVEMENT REPORT
========================================

📊 SUMMARY:
- Total Strains Processed: {total_strains}
- Invalid Strains Removed: {improvements.get('invalid_strains_removed', 0)}

🔧 IMPROVEMENTS MADE:
- Strain Names Cleaned: {improvements.get('names_cleaned', 0)}
- THC Percentages Extracted: {improvements.get('thc_extracted', 0)}
- CBD Percentages Extracted: {improvements.get('cbd_extracted', 0)}
- Strain Images Added: {improvements.get('images_added', 0)}

📈 DATA QUALITY:
- Strains with THC Data: {len([s for s in improved_data.get('strains', []) if s.get('thc_content')])}
- Strains with CBD Data: {len([s for s in improved_data.get('strains', []) if s.get('cbd_content')])}
- Strains with Images: {len([s for s in improved_data.get('strains', []) if s.get('image_url')])}

✅ All data has been cleaned and optimized for better accuracy!
"""
        return report

async def main():
    """Main function to improve existing strain data"""
    scraper = ImprovedStrainScraper()
    
    # File paths
    input_file = "data/enhanced_strains_1500.json"
    output_file = "data/improved_strains.json"
    
    print("🌿 Starting GrowWiz Strain Data Improvement...")
    
    # Improve existing data
    improved_data = await scraper.improve_existing_data(input_file, output_file)
    
    if improved_data:
        # Generate and display report
        report = scraper.generate_summary_report(improved_data)
        print(report)
        
        # Backup to Google Drive
        await scraper.backup_to_gdrive(output_file)
        
        print("✅ Strain data improvement completed successfully!")
    else:
        print("❌ Failed to improve strain data")

if __name__ == "__main__":
    asyncio.run(main())