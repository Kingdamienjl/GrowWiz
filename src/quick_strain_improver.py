#!/usr/bin/env python3
"""
Quick Strain Data Improver
Efficiently improves existing strain data by:
1. Extracting THC/CBD percentages from descriptions
2. Cleaning strain names (removing redundant suffixes)
3. Adding image_url field for future enhancement
"""

import json
import re
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ImprovedStrainData:
    name: str
    strain_type: str
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
    image_url: Optional[str] = None

class QuickStrainImprover:
    def __init__(self):
        # THC extraction patterns
        self.thc_patterns = [
            r'THC:\s*(\d+(?:\.\d+)?)\s*%',
            r'THC\s*(\d+(?:\.\d+)?)\s*%',
            r'(\d+(?:\.\d+)?)\s*%\s*THC',
            r'THC\s*levels?\s*(?:of\s*)?(\d+(?:\.\d+)?)\s*%',
            r'(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)\s*%\s*THC',
            r'THC\s*content\s*(?:of\s*)?(\d+(?:\.\d+)?)\s*%',
            r'contains?\s*(\d+(?:\.\d+)?)\s*%\s*THC',
            r'up\s*to\s*(\d+(?:\.\d+)?)\s*%\s*THC',
            r'around\s*(\d+(?:\.\d+)?)\s*%\s*THC',
            r'approximately\s*(\d+(?:\.\d+)?)\s*%\s*THC'
        ]
        
        # CBD extraction patterns
        self.cbd_patterns = [
            r'CBD:\s*(\d+(?:\.\d+)?)\s*%',
            r'CBD\s*(\d+(?:\.\d+)?)\s*%',
            r'(\d+(?:\.\d+)?)\s*%\s*CBD',
            r'CBD\s*levels?\s*(?:of\s*)?(\d+(?:\.\d+)?)\s*%',
            r'(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)\s*%\s*CBD',
            r'CBD\s*content\s*(?:of\s*)?(\d+(?:\.\d+)?)\s*%',
            r'contains?\s*(\d+(?:\.\d+)?)\s*%\s*CBD'
        ]
        
        # Name cleaning patterns
        self.name_suffixes = [
            r'\s+Marijuana\s+Strain$',
            r'\s+Cannabis\s+Strain$',
            r'\s+Weed\s+Strain$',
            r'\s+Strain$',
            r'\s+marijuana$',
            r'\s+cannabis$',
            r'\s+weed$'
        ]

    def clean_strain_name(self, name: str) -> str:
        """Clean strain name by removing redundant suffixes"""
        if not name:
            return ""
        
        cleaned = name.strip()
        
        # Remove common suffixes
        for pattern in self.name_suffixes:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        cleaned = ' '.join(cleaned.split())
        
        return cleaned

    def extract_thc_from_description(self, description: str) -> Optional[str]:
        """Extract THC percentage from description text"""
        if not description:
            return None
        
        for pattern in self.thc_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                # Handle range patterns (group 2 exists)
                if len(match.groups()) > 1 and match.group(2):
                    return f"{match.group(1)}-{match.group(2)}%"
                else:
                    return f"{match.group(1)}%"
        
        return None

    def extract_cbd_from_description(self, description: str) -> Optional[str]:
        """Extract CBD percentage from description text"""
        if not description:
            return None
        
        for pattern in self.cbd_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                # Handle range patterns
                if len(match.groups()) > 1 and match.group(2):
                    return f"{match.group(1)}-{match.group(2)}%"
                else:
                    return f"{match.group(1)}%"
        
        return None

    def improve_strain_data(self, input_file: str, output_file: str) -> bool:
        """Improve existing strain data"""
        try:
            print(f"🌿 Loading strain data from {input_file}...")
            
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            strains = data.get('strains', [])
            improved_strains = []
            
            # Track improvements
            stats = {
                'total_processed': 0,
                'names_cleaned': 0,
                'thc_extracted': 0,
                'cbd_extracted': 0,
                'invalid_removed': 0
            }
            
            print(f"📊 Processing {len(strains)} strains...")
            
            for i, strain in enumerate(strains):
                # Progress indicator
                if i % 50 == 0 and i > 0:
                    print(f"   Processed {i}/{len(strains)} strains...")
                
                # Skip invalid entries
                original_name = strain.get('name', '')
                if not original_name or original_name in [
                    'Find the perfect strain for you.',
                    'Indica Marijuana Strains with Information, Photos & Reviews'
                ]:
                    stats['invalid_removed'] += 1
                    continue
                
                # Clean strain name
                cleaned_name = self.clean_strain_name(original_name)
                if cleaned_name != original_name:
                    stats['names_cleaned'] += 1
                
                # Extract THC/CBD from description
                description = strain.get('description', '') or ''
                
                # Use existing values or extract from description
                thc_content = strain.get('thc_content')
                cbd_content = strain.get('cbd_content')
                
                if not thc_content:
                    extracted_thc = self.extract_thc_from_description(description)
                    if extracted_thc:
                        thc_content = extracted_thc
                        stats['thc_extracted'] += 1
                
                if not cbd_content:
                    extracted_cbd = self.extract_cbd_from_description(description)
                    if extracted_cbd:
                        cbd_content = extracted_cbd
                        stats['cbd_extracted'] += 1
                
                # Create improved strain data
                improved_strain = {
                    'name': cleaned_name,
                    'strain_type': strain.get('strain_type', ''),
                    'thc_content': thc_content,
                    'cbd_content': cbd_content,
                    'genetics': strain.get('genetics'),
                    'flowering_time': strain.get('flowering_time'),
                    'yield_info': strain.get('yield_info'),
                    'effects': strain.get('effects', []),
                    'medical_uses': strain.get('medical_uses', []),
                    'flavors': strain.get('flavors', []),
                    'aromas': strain.get('aromas', []),
                    'growing_difficulty': strain.get('growing_difficulty'),
                    'height': strain.get('height'),
                    'climate': strain.get('climate'),
                    'description': description,
                    'breeder': strain.get('breeder'),
                    'awards': strain.get('awards', []),
                    'source_url': strain.get('source_url'),
                    'scraped_at': strain.get('scraped_at'),
                    'popularity_score': strain.get('popularity_score'),
                    'price_range': strain.get('price_range'),
                    'seed_availability': strain.get('seed_availability'),
                    'grow_tips': strain.get('grow_tips', []),
                    'harvest_weight': strain.get('harvest_weight'),
                    'flowering_type': strain.get('flowering_type'),
                    'resistance': strain.get('resistance', []),
                    'terpenes': strain.get('terpenes', []),
                    'lineage': strain.get('lineage'),
                    'image_url': None  # Placeholder for future enhancement
                }
                
                improved_strains.append(improved_strain)
                stats['total_processed'] += 1
            
            # Create output data
            output_data = {
                'scraped_at': datetime.now().isoformat(),
                'total_strains': len(improved_strains),
                'improvement_stats': stats,
                'improvements_applied': [
                    'Extracted THC/CBD percentages from descriptions',
                    'Cleaned strain names (removed redundant suffixes)',
                    'Added image_url field for future enhancement',
                    'Removed invalid/duplicate entries'
                ],
                'strains': improved_strains
            }
            
            # Save improved data
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Improvement complete!")
            print(f"   📈 Stats:")
            print(f"      • Total strains processed: {stats['total_processed']}")
            print(f"      • Names cleaned: {stats['names_cleaned']}")
            print(f"      • THC values extracted: {stats['thc_extracted']}")
            print(f"      • CBD values extracted: {stats['cbd_extracted']}")
            print(f"      • Invalid entries removed: {stats['invalid_removed']}")
            print(f"   💾 Saved to: {output_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error improving strain data: {e}")
            return False

def main():
    print("🌿 GrowWiz Quick Strain Data Improver")
    print("=" * 50)
    
    improver = QuickStrainImprover()
    
    input_file = "data/enhanced_strains_1500.json"
    output_file = "data/improved_strains.json"
    
    success = improver.improve_strain_data(input_file, output_file)
    
    if success:
        print("\n🎉 Strain data improvement completed successfully!")
        print(f"📁 Check the improved data at: {output_file}")
    else:
        print("\n❌ Strain data improvement failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())