#!/usr/bin/env python3
"""
Final Strain Data Reconstructor
Comprehensive solution for reconstructing strain data with:
- THC/CBD extraction from descriptions
- Clean strain names (no "Marijuana Strain" suffix)
- Strain bud images
- Google Drive backup
"""

import json
import re
import logging
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import random
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from pathlib import Path

# Import Google Drive manager
try:
    from gdrive_manager import GDriveStrainManager
    GDRIVE_AVAILABLE = True
except ImportError:
    GDRIVE_AVAILABLE = False
    print("⚠️  Google Drive operations not available")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ReconstructedStrainData:
    """Enhanced strain data structure"""
    name: str
    strain_type: Optional[str] = None
    thc_content: Optional[str] = None
    cbd_content: Optional[str] = None
    description: Optional[str] = None
    effects: Optional[str] = None
    medical_uses: Optional[str] = None
    flavors: Optional[str] = None
    image_url: Optional[str] = None
    source_url: Optional[str] = None

class FinalStrainReconstructor:
    def __init__(self):
        self.session = None
        self.gdrive_manager = None
        
        # Initialize Google Drive if available
        if GDRIVE_AVAILABLE:
            try:
                self.gdrive_manager = GDriveStrainManager()
                print("✅ Google Drive manager initialized")
            except Exception as e:
                print(f"⚠️  Google Drive initialization failed: {e}")
                self.gdrive_manager = None
        
        # HTTP headers for web scraping
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive'
        }
        
        # THC/CBD extraction patterns
        self.thc_patterns = [
            r'THC[:\s]*(\d+(?:\.\d+)?)\s*%',
            r'(\d+(?:\.\d+)?)\s*%\s*THC',
            r'THC[:\s]*(\d+(?:\.\d+)?)',
            r'thc[:\s]*(\d+(?:\.\d+)?)\s*%',
            r'(\d+(?:\.\d+)?)\s*%\s*thc'
        ]
        
        self.cbd_patterns = [
            r'CBD[:\s]*(\d+(?:\.\d+)?)\s*%',
            r'(\d+(?:\.\d+)?)\s*%\s*CBD',
            r'CBD[:\s]*(\d+(?:\.\d+)?)',
            r'cbd[:\s]*(\d+(?:\.\d+)?)\s*%',
            r'(\d+(?:\.\d+)?)\s*%\s*cbd'
        ]
        
        # Image search sources
        self.image_sources = [
            "https://www.leafly.com/strains/{strain_name}",
            "https://www.allbud.com/marijuana-strains/search?q={strain_name}",
            "https://www.wikileaf.com/strain/{strain_name}"
        ]
        
        # Image selectors
        self.image_selectors = [
            'img[alt*="strain"]',
            'img[alt*="bud"]',
            'img[alt*="cannabis"]',
            '.strain-image img',
            '.bud-image img',
            '.product-image img',
            'img[src*="strain"]',
            'img[src*="bud"]'
        ]

    def clean_strain_name(self, name: str) -> str:
        """Clean strain name by removing redundant suffixes"""
        if not name:
            return name
        
        # Remove common suffixes
        suffixes_to_remove = [
            r'\s+marijuana\s+strain$',
            r'\s+strain$',
            r'\s+cannabis\s+strain$',
            r'\s+weed\s+strain$'
        ]
        
        cleaned_name = name
        for suffix in suffixes_to_remove:
            cleaned_name = re.sub(suffix, '', cleaned_name, flags=re.IGNORECASE)
        
        return cleaned_name.strip()

    def extract_thc_content(self, text: str) -> Optional[str]:
        """Extract THC percentage from text"""
        if not text:
            return None
        
        for pattern in self.thc_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                percentage = float(match.group(1))
                if 0 <= percentage <= 40:  # Reasonable THC range
                    return f"{percentage}%"
        
        return None

    def extract_cbd_content(self, text: str) -> Optional[str]:
        """Extract CBD percentage from text"""
        if not text:
            return None
        
        for pattern in self.cbd_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                percentage = float(match.group(1))
                if 0 <= percentage <= 30:  # Reasonable CBD range
                    return f"{percentage}%"
        
        return None

    def is_valid_strain_entry(self, strain: Dict[str, Any]) -> bool:
        """Check if strain entry is valid"""
        name = strain.get('name', '').strip()
        
        if not name:
            return False
        
        # Filter out generic entries
        invalid_patterns = [
            r'^find\s+the\s+perfect\s+strain',
            r'marijuana\s+strains\s+with\s+information',
            r'indica\s+marijuana\s+strains',
            r'sativa\s+marijuana\s+strains',
            r'hybrid\s+marijuana\s+strains',
            r'^\s*$'
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                return False
        
        return True

    def clean_strain_name_for_url(self, strain_name: str) -> str:
        """Clean strain name for URL usage"""
        cleaned = strain_name.lower()
        cleaned = re.sub(r'[^a-z0-9\s-]', '', cleaned)
        cleaned = re.sub(r'\s+', '-', cleaned)
        cleaned = re.sub(r'-+', '-', cleaned)
        return cleaned.strip('-')

    async def create_session(self):
        """Create aiohttp session"""
        connector = aiohttp.TCPConnector(limit=5, limit_per_host=2)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.headers
        )

    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()

    async def fetch_page(self, url: str) -> Optional[str]:
        """Fetch webpage content"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                return None
        except Exception as e:
            logger.debug(f"Error fetching {url}: {e}")
            return None

    def extract_images_from_html(self, html: str, base_url: str) -> List[str]:
        """Extract strain images from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            image_urls = []
            
            for selector in self.image_selectors:
                images = soup.select(selector)
                for img in images:
                    src = img.get('src') or img.get('data-src')
                    if src:
                        full_url = urljoin(base_url, src)
                        if self.is_valid_image_url(full_url):
                            image_urls.append(full_url)
            
            return list(dict.fromkeys(image_urls))[:2]  # Return top 2 unique images
            
        except Exception as e:
            logger.debug(f"Error extracting images: {e}")
            return []

    def is_valid_image_url(self, url: str) -> bool:
        """Check if URL is a valid strain image"""
        try:
            parsed = urlparse(url)
            path = parsed.path.lower()
            
            # Check for image extensions
            image_extensions = ['.jpg', '.jpeg', '.png', '.webp']
            has_extension = any(path.endswith(ext) for ext in image_extensions)
            
            # Check for strain-related keywords
            strain_keywords = ['strain', 'bud', 'cannabis', 'marijuana']
            has_keywords = any(keyword in url.lower() for keyword in strain_keywords)
            
            # Avoid non-strain images
            avoid_keywords = ['logo', 'icon', 'avatar', 'banner']
            has_avoid = any(keyword in url.lower() for keyword in avoid_keywords)
            
            return (has_extension or has_keywords) and not has_avoid and len(url) > 20
            
        except Exception:
            return False

    async def search_strain_image(self, strain_name: str) -> Optional[str]:
        """Search for a strain bud image"""
        cleaned_name = self.clean_strain_name_for_url(strain_name)
        
        for source_template in self.image_sources:
            try:
                url = source_template.format(strain_name=cleaned_name)
                html = await self.fetch_page(url)
                
                if html:
                    images = self.extract_images_from_html(html, url)
                    if images:
                        return images[0]
                
                # Rate limiting
                await asyncio.sleep(random.uniform(1, 2))
                
            except Exception as e:
                logger.debug(f"Error searching image for {strain_name}: {e}")
                continue
        
        return None

    def reconstruct_strain_data(self, original_strain: Dict[str, Any]) -> Optional[ReconstructedStrainData]:
        """Reconstruct a single strain's data"""
        try:
            # Extract basic info
            name = original_strain.get('name', '').strip()
            description = original_strain.get('description', '') or ''
            
            # Clean the strain name
            cleaned_name = self.clean_strain_name(name)
            
            # Extract THC/CBD from existing fields or description
            thc_content = original_strain.get('thc_content')
            cbd_content = original_strain.get('cbd_content')
            
            # If THC/CBD are null, extract from description
            if not thc_content or thc_content == 'null':
                thc_content = self.extract_thc_content(description)
            
            if not cbd_content or cbd_content == 'null':
                cbd_content = self.extract_cbd_content(description)
            
            # Create reconstructed strain data
            reconstructed = ReconstructedStrainData(
                name=cleaned_name,
                strain_type=original_strain.get('strain_type'),
                thc_content=thc_content,
                cbd_content=cbd_content,
                description=description,
                effects=original_strain.get('effects'),
                medical_uses=original_strain.get('medical_uses'),
                flavors=original_strain.get('flavors'),
                source_url=original_strain.get('source_url')
            )
            
            return reconstructed
            
        except Exception as e:
            logger.error(f"Error reconstructing strain data: {e}")
            return None

    async def reconstruct_all_strains(self, input_file: str, output_file: str, add_images: bool = True, max_strains: int = None) -> bool:
        """Reconstruct all strain data"""
        try:
            print(f"🔧 Loading strain data from {input_file}...")
            
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            original_strains = data.get('strains', [])
            
            # Limit processing if specified
            if max_strains:
                original_strains = original_strains[:max_strains]
            
            print(f"📊 Processing {len(original_strains)} strains...")
            
            # Filter valid strains and reconstruct
            reconstructed_strains = []
            names_cleaned = 0
            thc_extracted = 0
            cbd_extracted = 0
            invalid_removed = 0
            
            for i, strain in enumerate(original_strains):
                if not self.is_valid_strain_entry(strain):
                    invalid_removed += 1
                    continue
                
                reconstructed = self.reconstruct_strain_data(strain)
                if reconstructed:
                    # Track improvements
                    original_name = strain.get('name', '')
                    if original_name != reconstructed.name:
                        names_cleaned += 1
                    
                    if reconstructed.thc_content and not strain.get('thc_content'):
                        thc_extracted += 1
                    
                    if reconstructed.cbd_content and not strain.get('cbd_content'):
                        cbd_extracted += 1
                    
                    reconstructed_strains.append(asdict(reconstructed))
                
                if (i + 1) % 50 == 0:
                    print(f"   Processed {i + 1}/{len(original_strains)} strains...")
            
            print(f"✅ Data reconstruction complete!")
            print(f"   📝 Names cleaned: {names_cleaned}")
            print(f"   🌿 THC values extracted: {thc_extracted}")
            print(f"   💊 CBD values extracted: {cbd_extracted}")
            print(f"   🗑️  Invalid entries removed: {invalid_removed}")
            
            # Add images if requested
            if add_images and len(reconstructed_strains) > 0:
                print(f"\n🖼️  Searching for strain bud images...")
                await self.create_session()
                
                images_found = 0
                # Process first 30 strains for images (to avoid rate limiting)
                strains_for_images = reconstructed_strains[:min(30, len(reconstructed_strains))]
                
                for i, strain in enumerate(strains_for_images):
                    strain_name = strain['name']
                    print(f"   [{i+1}/{len(strains_for_images)}] Searching image for {strain_name}...")
                    
                    image_url = await self.search_strain_image(strain_name)
                    if image_url:
                        strain['image_url'] = image_url
                        images_found += 1
                        print(f"      ✅ Found: {image_url[:60]}...")
                    else:
                        print(f"      ❌ No image found")
                    
                    # Rate limiting
                    await asyncio.sleep(random.uniform(2, 4))
                
                await self.close_session()
                print(f"🖼️  Images found: {images_found}/{len(strains_for_images)}")
            
            # Prepare final data structure
            final_data = {
                'metadata': {
                    'total_strains': len(reconstructed_strains),
                    'names_cleaned': names_cleaned,
                    'thc_extracted': thc_extracted,
                    'cbd_extracted': cbd_extracted,
                    'invalid_removed': invalid_removed,
                    'images_added': images_found if add_images else 0,
                    'reconstruction_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'source_file': input_file
                },
                'strains': reconstructed_strains
            }
            
            # Save reconstructed data
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Reconstructed data saved to: {output_file}")
            
            # Backup to Google Drive
            if self.gdrive_manager:
                print(f"\n☁️  Backing up to Google Drive...")
                try:
                    self.gdrive_manager.organize_strains_to_drive(reconstructed_strains)
                    print(f"✅ Google Drive backup completed!")
                except Exception as e:
                    print(f"❌ Google Drive backup failed: {e}")
            else:
                print(f"⚠️  Google Drive backup skipped (not available)")
            
            return True
            
        except Exception as e:
            logger.error(f"Error reconstructing strain data: {e}")
            return False

async def main():
    print("🔧 GrowWiz Final Strain Data Reconstructor")
    print("=" * 60)
    print("Features:")
    print("  ✅ Extract THC/CBD from descriptions")
    print("  ✅ Clean strain names (remove 'Marijuana Strain' suffix)")
    print("  ✅ Add strain bud images")
    print("  ✅ Google Drive backup")
    print("=" * 60)
    
    reconstructor = FinalStrainReconstructor()
    
    input_file = "data/enhanced_strains_1500.json"
    output_file = "data/final_reconstructed_strains.json"
    
    # Process all strains with images for first 30
    success = await reconstructor.reconstruct_all_strains(
        input_file=input_file,
        output_file=output_file,
        add_images=True,
        max_strains=None  # Process all strains
    )
    
    if success:
        print(f"\n🎉 Strain data reconstruction completed successfully!")
        print(f"📁 Final data available at: {output_file}")
        print(f"☁️  Data backed up to Google Drive (if available)")
    else:
        print(f"\n❌ Strain data reconstruction failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    asyncio.run(main())