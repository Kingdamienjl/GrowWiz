#!/usr/bin/env python3
"""
Strain Image Scraper
Adds strain bud images to the improved strain data using web scraping
"""

import json
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import logging
from typing import Optional, List, Dict
import time
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

class StrainImageScraper:
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Image selectors for different sites
        self.image_selectors = [
            'img[alt*="strain"]',
            'img[alt*="bud"]',
            'img[alt*="cannabis"]',
            'img[alt*="marijuana"]',
            '.strain-image img',
            '.bud-image img',
            '.product-image img',
            '.strain-photo img',
            'img[src*="strain"]',
            'img[src*="bud"]',
            'img[src*="cannabis"]',
            '.gallery img',
            '.strain-gallery img',
            'img.strain',
            'img.bud-photo'
        ]
        
        # Common image search engines for strain images
        self.image_sources = [
            "https://www.leafly.com/strains/{strain_name}",
            "https://www.allbud.com/marijuana-strains/search?q={strain_name}",
            "https://www.wikileaf.com/strain/{strain_name}",
            "https://www.ilovegrowingmarijuana.com/strain/{strain_name}",
            "https://www.seedsman.com/en/search?q={strain_name}"
        ]

    async def create_session(self):
        """Create aiohttp session"""
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
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

    def clean_strain_name_for_url(self, strain_name: str) -> str:
        """Clean strain name for URL usage"""
        # Convert to lowercase and replace spaces with hyphens
        cleaned = strain_name.lower()
        cleaned = re.sub(r'[^a-z0-9\s-]', '', cleaned)
        cleaned = re.sub(r'\s+', '-', cleaned)
        cleaned = re.sub(r'-+', '-', cleaned)
        return cleaned.strip('-')

    async def fetch_page(self, url: str) -> Optional[str]:
        """Fetch webpage content"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.debug(f"Failed to fetch {url}: Status {response.status}")
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
                    src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                    if src:
                        # Convert relative URLs to absolute
                        full_url = urljoin(base_url, src)
                        
                        # Filter for actual image files
                        if self.is_valid_image_url(full_url):
                            image_urls.append(full_url)
            
            # Remove duplicates and return first few
            unique_images = list(dict.fromkeys(image_urls))
            return unique_images[:3]  # Return top 3 images
            
        except Exception as e:
            logger.debug(f"Error extracting images: {e}")
            return []

    def is_valid_image_url(self, url: str) -> bool:
        """Check if URL is a valid image"""
        try:
            parsed = urlparse(url)
            path = parsed.path.lower()
            
            # Check for image extensions
            image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
            has_extension = any(path.endswith(ext) for ext in image_extensions)
            
            # Check for image-related keywords
            image_keywords = ['strain', 'bud', 'cannabis', 'marijuana', 'weed', 'photo', 'image']
            has_keywords = any(keyword in url.lower() for keyword in image_keywords)
            
            # Avoid common non-strain images
            avoid_keywords = ['logo', 'icon', 'avatar', 'banner', 'ad', 'advertisement']
            has_avoid = any(keyword in url.lower() for keyword in avoid_keywords)
            
            return (has_extension or has_keywords) and not has_avoid and len(url) > 20
            
        except Exception:
            return False

    async def search_strain_images(self, strain_name: str) -> Optional[str]:
        """Search for strain images across multiple sources"""
        cleaned_name = self.clean_strain_name_for_url(strain_name)
        
        for source_template in self.image_sources:
            try:
                # Format URL with strain name
                url = source_template.format(strain_name=cleaned_name)
                
                logger.debug(f"Searching for {strain_name} images at: {url}")
                
                # Fetch page content
                html = await self.fetch_page(url)
                if not html:
                    continue
                
                # Extract images
                images = self.extract_images_from_html(html, url)
                if images:
                    logger.debug(f"Found {len(images)} images for {strain_name}")
                    return images[0]  # Return the first/best image
                
                # Add delay between requests
                await asyncio.sleep(random.uniform(1, 3))
                
            except Exception as e:
                logger.debug(f"Error searching {source_template}: {e}")
                continue
        
        return None

    async def add_images_to_strains(self, input_file: str, output_file: str, max_strains: int = 50) -> bool:
        """Add images to strain data"""
        try:
            print(f"🖼️  Loading strain data from {input_file}...")
            
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            strains = data.get('strains', [])
            
            # Limit processing for testing
            strains_to_process = strains[:max_strains]
            
            print(f"🔍 Searching for images for {len(strains_to_process)} strains...")
            
            await self.create_session()
            
            images_found = 0
            
            for i, strain in enumerate(strains_to_process):
                strain_name = strain.get('name', '')
                if not strain_name:
                    continue
                
                print(f"   [{i+1}/{len(strains_to_process)}] Searching for {strain_name}...")
                
                # Search for strain image
                image_url = await self.search_strain_images(strain_name)
                
                if image_url:
                    strain['image_url'] = image_url
                    images_found += 1
                    print(f"      ✅ Found image: {image_url[:80]}...")
                else:
                    print(f"      ❌ No image found")
                
                # Add delay between strains
                await asyncio.sleep(random.uniform(2, 4))
            
            await self.close_session()
            
            # Update metadata
            data['image_search_completed'] = True
            data['images_found'] = images_found
            data['strains_processed_for_images'] = len(strains_to_process)
            
            # Save updated data
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Image search complete!")
            print(f"   📊 Found images for {images_found}/{len(strains_to_process)} strains")
            print(f"   💾 Saved to: {output_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding images to strains: {e}")
            return False

async def main():
    print("🖼️  GrowWiz Strain Image Scraper")
    print("=" * 50)
    
    scraper = StrainImageScraper()
    
    input_file = "data/improved_strains.json"
    output_file = "data/improved_strains_with_images.json"
    
    # Process first 20 strains as a test
    success = await scraper.add_images_to_strains(input_file, output_file, max_strains=20)
    
    if success:
        print("\n🎉 Strain image scraping completed successfully!")
        print(f"📁 Check the enhanced data at: {output_file}")
    else:
        print("\n❌ Strain image scraping failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    asyncio.run(main())