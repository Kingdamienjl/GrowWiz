#!/usr/bin/env python3
"""
Enhanced Strain Image Downloader
Downloads actual strain bud images and saves them locally for computer vision training
"""

import json
import asyncio
import aiohttp
import aiofiles
import os
from pathlib import Path
import hashlib
from urllib.parse import urlparse
import logging
from typing import Optional, List, Dict
import time
import random
from PIL import Image
import io

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

class StrainImageDownloader:
    def __init__(self, images_dir: str = "data/strain_images"):
        self.images_dir = Path(images_dir)
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.session = None
        
        # More realistic headers to avoid detection
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'image',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Site': 'cross-site',
            'Cache-Control': 'no-cache'
        }
        
        # Alternative image search APIs and sources
        self.image_sources = [
            # Google Images API (requires API key but more reliable)
            "https://www.googleapis.com/customsearch/v1?key={api_key}&cx={cx}&q={strain_name}+cannabis+strain+bud&searchType=image&num=3",
            
            # Bing Image Search API
            "https://api.bing.microsoft.com/v7.0/images/search?q={strain_name}+cannabis+strain+bud&count=3",
            
            # Direct strain database sites with better image access
            "https://www.leafly.com/api/strains/{strain_name}/photos",
            "https://www.seedfinder.eu/strain-info/{strain_name}/pictures/",
            
            # Cannabis community sites
            "https://www.growdiaries.com/diaries/search?strain={strain_name}",
            "https://www.ilovegrowingmarijuana.com/strain/{strain_name}/",
        ]

    async def create_session(self):
        """Create aiohttp session with proper configuration"""
        connector = aiohttp.TCPConnector(
            limit=5,
            limit_per_host=2,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        timeout = aiohttp.ClientTimeout(total=60, connect=30)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.headers
        )

    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()

    def clean_strain_name(self, strain_name: str) -> str:
        """Clean strain name for file naming"""
        import re
        cleaned = re.sub(r'[^\w\s-]', '', strain_name.lower())
        cleaned = re.sub(r'\s+', '_', cleaned)
        return cleaned.strip('_')

    def get_image_filename(self, strain_name: str, image_url: str, index: int = 0) -> str:
        """Generate unique filename for strain image"""
        clean_name = self.clean_strain_name(strain_name)
        url_hash = hashlib.md5(image_url.encode()).hexdigest()[:8]
        extension = self.get_image_extension(image_url)
        return f"{clean_name}_{index}_{url_hash}.{extension}"

    def get_image_extension(self, url: str) -> str:
        """Extract image extension from URL"""
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        if path.endswith('.jpg') or path.endswith('.jpeg'):
            return 'jpg'
        elif path.endswith('.png'):
            return 'png'
        elif path.endswith('.webp'):
            return 'webp'
        else:
            return 'jpg'  # Default

    async def download_image(self, url: str, filepath: Path) -> bool:
        """Download image from URL and save locally"""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    
                    # Validate it's actually an image
                    try:
                        img = Image.open(io.BytesIO(content))
                        
                        # Skip tiny images (likely placeholders)
                        if img.width < 100 or img.height < 100:
                            logger.debug(f"Skipping tiny image: {img.width}x{img.height}")
                            return False
                        
                        # Convert to RGB if necessary and save as JPEG
                        if img.mode in ('RGBA', 'LA', 'P'):
                            img = img.convert('RGB')
                        
                        # Save with compression
                        img.save(filepath, 'JPEG', quality=85, optimize=True)
                        logger.info(f"Downloaded image: {filepath.name} ({img.width}x{img.height})")
                        return True
                        
                    except Exception as e:
                        logger.debug(f"Invalid image content from {url}: {e}")
                        return False
                else:
                    logger.debug(f"Failed to download {url}: Status {response.status}")
                    return False
                    
        except Exception as e:
            logger.debug(f"Error downloading {url}: {e}")
            return False

    async def search_strain_images_duckduckgo(self, strain_name: str) -> List[str]:
        """Search for strain images using DuckDuckGo (no API key required)"""
        try:
            # DuckDuckGo instant answer API for images
            search_url = f"https://duckduckgo.com/?q={strain_name}+cannabis+strain+bud&t=h_&iax=images&ia=images&format=json"
            
            async with self.session.get(search_url) as response:
                if response.status == 200:
                    # DuckDuckGo requires a different approach - let's use a simpler method
                    pass
            
            # For now, let's use a curated list of high-quality strain image URLs
            # This would be replaced with actual API calls in production
            sample_images = [
                f"https://images.leafly.com/flower-images/{self.clean_strain_name(strain_name)}/primary?width=400&height=400",
                f"https://www.allbud.com/marijuana-strains/photos/{self.clean_strain_name(strain_name)}.jpg",
                f"https://www.wikileaf.com/thestash/wp-content/uploads/2019/01/{self.clean_strain_name(strain_name)}.jpg"
            ]
            
            return sample_images[:2]  # Return 2 potential URLs
            
        except Exception as e:
            logger.debug(f"Error searching for {strain_name}: {e}")
            return []

    async def generate_synthetic_strain_image(self, strain_name: str, strain_data: Dict) -> Optional[str]:
        """Generate a synthetic strain image based on strain characteristics"""
        try:
            # Create a simple visualization based on strain data
            from PIL import Image, ImageDraw, ImageFont
            
            # Create base image
            img = Image.new('RGB', (400, 400), color='#2d5016')  # Dark green background
            draw = ImageDraw.Draw(img)
            
            # Add strain name
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            # Draw strain name
            draw.text((20, 20), strain_name, fill='white', font=font)
            
            # Add strain type indicator
            strain_type = strain_data.get('strain_type', 'hybrid')
            type_colors = {
                'indica': '#4a0e4e',      # Purple
                'sativa': '#ff6b35',      # Orange
                'hybrid': '#2d5016'       # Green
            }
            
            color = type_colors.get(strain_type, '#2d5016')
            draw.rectangle([20, 60, 380, 100], fill=color)
            draw.text((30, 70), f"Type: {strain_type.title()}", fill='white', font=font)
            
            # Add THC content if available
            thc = strain_data.get('thc_content', 'Unknown')
            draw.text((30, 120), f"THC: {thc}", fill='white', font=font)
            
            # Save synthetic image
            filename = f"{self.clean_strain_name(strain_name)}_synthetic.jpg"
            filepath = self.images_dir / filename
            img.save(filepath, 'JPEG', quality=85)
            
            logger.info(f"Generated synthetic image: {filename}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error generating synthetic image for {strain_name}: {e}")
            return None

    async def download_strain_images(self, strain_name: str, strain_data: Dict) -> List[str]:
        """Download images for a specific strain"""
        downloaded_images = []
        
        # Try to find real images first
        image_urls = await self.search_strain_images_duckduckgo(strain_name)
        
        for i, url in enumerate(image_urls):
            filename = self.get_image_filename(strain_name, url, i)
            filepath = self.images_dir / filename
            
            if await self.download_image(url, filepath):
                downloaded_images.append(str(filepath))
                
            # Add delay between downloads
            await asyncio.sleep(random.uniform(1, 2))
        
        # If no real images found, generate synthetic one
        if not downloaded_images:
            synthetic_path = await self.generate_synthetic_strain_image(strain_name, strain_data)
            if synthetic_path:
                downloaded_images.append(synthetic_path)
        
        return downloaded_images

    async def process_strain_database(self, input_file: str, max_strains: int = 50) -> Dict:
        """Process strain database and download images"""
        try:
            print(f"🖼️  Loading strain data from {input_file}...")
            
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different data structures
            if isinstance(data, dict) and 'strains' in data:
                strains = data['strains']
            elif isinstance(data, list):
                strains = data
            else:
                strains = [data]
            
            # Limit processing for testing
            strains_to_process = strains[:max_strains]
            
            print(f"🔍 Downloading images for {len(strains_to_process)} strains...")
            
            await self.create_session()
            
            results = {
                'processed_strains': 0,
                'images_downloaded': 0,
                'synthetic_generated': 0,
                'failed_downloads': 0,
                'strain_images': {}
            }
            
            for i, strain in enumerate(strains_to_process):
                strain_name = strain.get('name', f'Unknown_{i}')
                print(f"   [{i+1}/{len(strains_to_process)}] Processing {strain_name}...")
                
                try:
                    images = await self.download_strain_images(strain_name, strain)
                    
                    if images:
                        results['strain_images'][strain_name] = images
                        results['images_downloaded'] += len([img for img in images if 'synthetic' not in img])
                        results['synthetic_generated'] += len([img for img in images if 'synthetic' in img])
                        print(f"      ✅ Got {len(images)} image(s)")
                    else:
                        results['failed_downloads'] += 1
                        print(f"      ❌ No images obtained")
                    
                    results['processed_strains'] += 1
                    
                    # Add delay between strains
                    await asyncio.sleep(random.uniform(2, 4))
                    
                except Exception as e:
                    logger.error(f"Error processing {strain_name}: {e}")
                    results['failed_downloads'] += 1
            
            await self.close_session()
            
            # Save results
            results_file = self.images_dir / 'download_results.json'
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ Image download complete!")
            print(f"   📊 Processed: {results['processed_strains']} strains")
            print(f"   🖼️  Downloaded: {results['images_downloaded']} real images")
            print(f"   🎨 Generated: {results['synthetic_generated']} synthetic images")
            print(f"   ❌ Failed: {results['failed_downloads']} strains")
            print(f"   💾 Images saved to: {self.images_dir}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing strain database: {e}")
            return {}

async def main():
    print("🖼️  GrowWiz Enhanced Strain Image Downloader")
    print("=" * 50)
    
    downloader = StrainImageDownloader()
    
    # Use the enhanced strain data
    input_file = "data/enhanced_strains_v2_635_20250805_104847.json"
    
    # Process first 20 strains as a test
    results = await downloader.process_strain_database(input_file, max_strains=20)
    
    if results:
        print("\n🎉 Strain image downloading completed!")
        print(f"📁 Check images at: {downloader.images_dir}")
        return 0
    else:
        print("\n❌ Strain image downloading failed!")
        return 1

if __name__ == "__main__":
    asyncio.run(main())