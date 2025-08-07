#!/usr/bin/env python3
"""
GrowWiz Strain Identifier
AI-powered strain identification from bud images
Extends the existing plant classifier for strain-specific recognition
"""

import os
import json
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import cv2
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from loguru import logger
import hashlib
from pathlib import Path
import pickle

class StrainIdentifier:
    def __init__(self, model_path: Optional[str] = None, strain_data_path: str = None):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = None
        self.strain_database = {}
        self.strain_classes = []
        self.feature_extractor = None
        self.simulation_mode = True  # Start in simulation mode
        
        # Load strain database
        self.load_strain_database(strain_data_path)
        
        # Initialize feature extraction
        self.transform = self._get_transform()
        
        # Try to load pre-trained model
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
        else:
            logger.info("No pre-trained strain model found, using simulation mode")

    def load_strain_database(self, data_path: str = None):
        """Load strain database for reference"""
        try:
            # Try to load from enhanced strain files first
            strain_files = [
                os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'enhanced_strains_v2_635_20250805_104847.json'),
                os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'final_reconstructed_strains.json'),
                os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'enhanced_strains_1500.json'),
                os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'strain_database.json')
            ]
            
            # Use provided path if given
            if data_path:
                strain_files.insert(0, data_path)
            
            for file_path in strain_files:
                if os.path.exists(file_path):
                    logger.info(f"Loading strain database from: {file_path}")
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Handle different data structures
                    if isinstance(data, dict) and 'strains' in data:
                        strains = data['strains']
                    elif isinstance(data, list):
                        strains = data
                    else:
                        strains = [data]
                    
                    # Build strain database
                    for strain in strains:
                        name = strain.get('name', '')
                        if name:
                            self.strain_database[name] = strain
                            self.strain_classes.append(name)
                            
                    logger.info(f"Loaded {len(self.strain_database)} strains from database")
                    self.simulation_mode = False
                    return
            
            # If no files found, use simulation mode
            logger.warning("No strain database files found, using simulation mode")
            self.simulation_mode = True
            self._create_simulation_database()
                
        except Exception as e:
            logger.error(f"Error loading strain database: {e}")
            self.simulation_mode = True
            self._create_simulation_database()
    
    def _create_simulation_database(self):
        """Create a simulation database with sample strains"""
        simulation_strains = [
            {
                "name": "Blue Dream",
                "strain_type": "Hybrid",
                "thc_content": "17-24%",
                "cbd_content": "0.1-0.2%",
                "effects": ["Euphoric", "Relaxed", "Creative"],
                "description": "Popular hybrid strain with balanced effects"
            },
            {
                "name": "OG Kush", 
                "strain_type": "Hybrid",
                "thc_content": "20-25%",
                "cbd_content": "0.1-0.3%",
                "effects": ["Euphoric", "Happy", "Relaxed"],
                "description": "Legendary strain with strong effects"
            },
            {
                "name": "Sour Diesel",
                "strain_type": "Sativa", 
                "thc_content": "20-25%",
                "cbd_content": "0.1-0.2%",
                "effects": ["Energetic", "Happy", "Creative"],
                "description": "Energizing sativa with diesel aroma"
            }
        ]
        
        for strain in simulation_strains:
            self.strain_database[strain['name']] = strain
            self.strain_classes.append(strain['name'])
            
        logger.info(f"Created simulation database with {len(simulation_strains)} strains")

    def _get_transform(self):
        """Get image preprocessing transforms optimized for strain identification"""
        return transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])

    def extract_visual_features(self, image_path: str) -> Dict[str, Any]:
        """Extract visual features specific to strain identification"""
        try:
            # Load image with OpenCV for advanced analysis
            img = cv2.imread(image_path)
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            features = {}
            
            # Color analysis - crucial for strain identification
            features.update(self._analyze_colors(img_rgb))
            
            # Texture analysis - trichome density, bud structure
            features.update(self._analyze_texture(img_rgb))
            
            # Shape analysis - bud density and structure
            features.update(self._analyze_shape(img_rgb))
            
            # Size analysis
            features['image_dimensions'] = {
                'width': img_rgb.shape[1],
                'height': img_rgb.shape[0]
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting visual features: {e}")
            return {}

    def _analyze_colors(self, img_rgb: np.ndarray) -> Dict[str, Any]:
        """Analyze color characteristics for strain identification"""
        try:
            # Convert to different color spaces
            hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
            lab = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2LAB)
            
            # Calculate color statistics
            rgb_mean = np.mean(img_rgb, axis=(0, 1))
            hsv_mean = np.mean(hsv, axis=(0, 1))
            
            # Detect dominant colors
            dominant_colors = self._get_dominant_colors(img_rgb)
            
            # Green analysis (healthy cannabis should be green)
            green_mask = cv2.inRange(hsv, (35, 40, 40), (85, 255, 255))
            green_percentage = (np.sum(green_mask > 0) / green_mask.size) * 100
            
            # Purple analysis (some strains have purple hues)
            purple_mask = cv2.inRange(hsv, (120, 40, 40), (160, 255, 255))
            purple_percentage = (np.sum(purple_mask > 0) / purple_mask.size) * 100
            
            # Orange/amber analysis (pistils and trichomes)
            orange_mask = cv2.inRange(hsv, (10, 100, 100), (25, 255, 255))
            orange_percentage = (np.sum(orange_mask > 0) / orange_mask.size) * 100
            
            return {
                'rgb_mean': rgb_mean.tolist(),
                'hsv_mean': hsv_mean.tolist(),
                'dominant_colors': dominant_colors,
                'green_percentage': green_percentage,
                'purple_percentage': purple_percentage,
                'orange_percentage': orange_percentage,
                'color_variance': np.var(img_rgb, axis=(0, 1)).tolist()
            }
            
        except Exception as e:
            logger.error(f"Error in color analysis: {e}")
            return {}

    def _analyze_texture(self, img_rgb: np.ndarray) -> Dict[str, Any]:
        """Analyze texture for trichome density and bud structure"""
        try:
            # Convert to grayscale for texture analysis
            gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
            
            # Calculate texture features using Local Binary Patterns
            from skimage.feature import local_binary_pattern
            
            # LBP parameters
            radius = 3
            n_points = 8 * radius
            lbp = local_binary_pattern(gray, n_points, radius, method='uniform')
            
            # Calculate LBP histogram
            lbp_hist, _ = np.histogram(lbp.ravel(), bins=n_points + 2, 
                                     range=(0, n_points + 2), density=True)
            
            # Edge detection for structure analysis
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            
            # Texture contrast using GLCM approximation
            contrast = np.std(gray)
            
            # Detect potential trichomes (bright spots)
            _, bright_spots = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
            trichome_density = np.sum(bright_spots > 0) / bright_spots.size * 100
            
            return {
                'lbp_histogram': lbp_hist.tolist(),
                'edge_density': edge_density,
                'texture_contrast': contrast,
                'trichome_density': trichome_density,
                'texture_uniformity': np.mean(lbp_hist)
            }
            
        except Exception as e:
            logger.error(f"Error in texture analysis: {e}")
            return {}

    def _analyze_shape(self, img_rgb: np.ndarray) -> Dict[str, Any]:
        """Analyze bud shape and structure"""
        try:
            # Convert to grayscale and apply threshold
            gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Find contours
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Get largest contour (main bud)
                largest_contour = max(contours, key=cv2.contourArea)
                
                # Calculate shape features
                area = cv2.contourArea(largest_contour)
                perimeter = cv2.arcLength(largest_contour, True)
                
                # Circularity (4π*area/perimeter²)
                circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter > 0 else 0
                
                # Aspect ratio
                x, y, w, h = cv2.boundingRect(largest_contour)
                aspect_ratio = w / h if h > 0 else 0
                
                # Solidity (area/convex_hull_area)
                hull = cv2.convexHull(largest_contour)
                hull_area = cv2.contourArea(hull)
                solidity = area / hull_area if hull_area > 0 else 0
                
                return {
                    'bud_area': area,
                    'bud_perimeter': perimeter,
                    'circularity': circularity,
                    'aspect_ratio': aspect_ratio,
                    'solidity': solidity,
                    'bounding_box': [x, y, w, h]
                }
            else:
                return {'bud_area': 0, 'bud_perimeter': 0, 'circularity': 0, 
                       'aspect_ratio': 0, 'solidity': 0, 'bounding_box': [0, 0, 0, 0]}
                
        except Exception as e:
            logger.error(f"Error in shape analysis: {e}")
            return {}

    def _get_dominant_colors(self, img_rgb: np.ndarray, k: int = 5) -> List[List[int]]:
        """Extract dominant colors using K-means clustering"""
        try:
            # Reshape image to be a list of pixels
            data = img_rgb.reshape((-1, 3))
            data = np.float32(data)
            
            # Apply K-means
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
            _, labels, centers = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            
            # Convert back to uint8 and return
            centers = np.uint8(centers)
            return centers.tolist()
            
        except Exception as e:
            logger.error(f"Error extracting dominant colors: {e}")
            return []

    def calculate_strain_similarity(self, features: Dict[str, Any], strain_name: str) -> float:
        """Calculate similarity between extracted features and known strain characteristics"""
        try:
            strain_data = self.strain_database.get(strain_name, {})
            
            similarity_score = 0.0
            total_weight = 0.0
            
            # Color-based similarity (weight: 0.4)
            color_weight = 0.4
            if 'green_percentage' in features:
                # Indica strains typically have darker, more purple hues
                # Sativa strains typically have brighter, more green hues
                strain_type = strain_data.get('strain_type', 'hybrid').lower()
                
                if strain_type == 'indica':
                    # Indica preference: more purple, less bright green
                    color_score = (features.get('purple_percentage', 0) * 0.6 + 
                                 (100 - features.get('green_percentage', 50)) * 0.4) / 100
                elif strain_type == 'sativa':
                    # Sativa preference: more green, less purple
                    color_score = (features.get('green_percentage', 50) * 0.6 + 
                                 (100 - features.get('purple_percentage', 0)) * 0.4) / 100
                else:  # hybrid
                    # Balanced color profile
                    color_score = (features.get('green_percentage', 50) + 
                                 features.get('purple_percentage', 0)) / 100
                
                similarity_score += color_score * color_weight
                total_weight += color_weight
            
            # THC content correlation (weight: 0.2)
            thc_weight = 0.2
            strain_thc = strain_data.get('thc_content', '')
            if strain_thc and '%' in strain_thc:
                try:
                    thc_value = float(strain_thc.replace('%', ''))
                    # Higher THC often correlates with more trichomes
                    trichome_density = features.get('trichome_density', 0)
                    expected_trichomes = min(thc_value * 2, 100)  # Rough correlation
                    thc_score = 1.0 - abs(trichome_density - expected_trichomes) / 100
                    similarity_score += max(0, thc_score) * thc_weight
                    total_weight += thc_weight
                except:
                    pass
            
            # Texture similarity (weight: 0.3)
            texture_weight = 0.3
            if 'texture_contrast' in features:
                # Different strains have different bud densities
                contrast = features.get('texture_contrast', 0)
                # Normalize contrast score
                texture_score = min(contrast / 100, 1.0)
                similarity_score += texture_score * texture_weight
                total_weight += texture_weight
            
            # Shape similarity (weight: 0.1)
            shape_weight = 0.1
            if 'circularity' in features:
                circularity = features.get('circularity', 0)
                # Most cannabis buds have moderate circularity
                ideal_circularity = 0.6
                shape_score = 1.0 - abs(circularity - ideal_circularity)
                similarity_score += max(0, shape_score) * shape_weight
                total_weight += shape_weight
            
            # Normalize final score
            if total_weight > 0:
                return similarity_score / total_weight
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculating similarity for {strain_name}: {e}")
            return 0.0

    def identify_strain(self, image_path: str, top_k: int = 5) -> Dict[str, Any]:
        """Main strain identification function"""
        try:
            if not os.path.exists(image_path):
                return {'error': f'Image file not found: {image_path}'}
            
            logger.info(f"Identifying strain from image: {image_path}")
            
            # Extract visual features
            features = self.extract_visual_features(image_path)
            
            if not features:
                return {'error': 'Failed to extract visual features from image'}
            
            # Calculate similarity scores for all strains
            strain_scores = []
            
            for strain_name in self.strain_classes:
                similarity = self.calculate_strain_similarity(features, strain_name)
                strain_scores.append({
                    'strain_name': strain_name,
                    'confidence': similarity,
                    'strain_data': self.strain_database.get(strain_name, {})
                })
            
            # Sort by confidence and get top results
            strain_scores.sort(key=lambda x: x['confidence'], reverse=True)
            top_matches = strain_scores[:top_k]
            
            # Prepare result
            result = {
                'image_path': image_path,
                'top_matches': top_matches,
                'primary_identification': top_matches[0] if top_matches else None,
                'visual_features': features,
                'identification_method': 'visual_feature_analysis',
                'total_strains_compared': len(self.strain_classes),
                'model_version': '1.0.0_simulation'
            }
            
            if top_matches:
                primary = top_matches[0]
                logger.info(f"Primary identification: {primary['strain_name']} "
                           f"(confidence: {primary['confidence']:.3f})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error identifying strain: {e}")
            return {'error': str(e)}

    def batch_identify_strains(self, image_directory: str) -> Dict[str, Any]:
        """Identify strains for all images in a directory"""
        try:
            image_dir = Path(image_directory)
            if not image_dir.exists():
                return {'error': f'Directory not found: {image_directory}'}
            
            # Find all image files
            image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
            image_files = [f for f in image_dir.iterdir() 
                          if f.suffix.lower() in image_extensions]
            
            results = {
                'processed_images': 0,
                'successful_identifications': 0,
                'failed_identifications': 0,
                'results': {}
            }
            
            for image_file in image_files:
                try:
                    result = self.identify_strain(str(image_file))
                    results['results'][image_file.name] = result
                    
                    if 'error' not in result:
                        results['successful_identifications'] += 1
                    else:
                        results['failed_identifications'] += 1
                    
                    results['processed_images'] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing {image_file}: {e}")
                    results['failed_identifications'] += 1
                    results['processed_images'] += 1
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch identification: {e}")
            return {'error': str(e)}

    def save_identification_results(self, results: Dict[str, Any], output_file: str):
        """Save identification results to JSON file"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"Results saved to: {output_file}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")

async def main():
    print("🔍 GrowWiz Strain Identifier")
    print("=" * 50)
    
    # Initialize strain identifier
    identifier = StrainIdentifier()
    
    # Test with synthetic images
    image_dir = "data/strain_images"
    
    if os.path.exists(image_dir):
        print(f"🖼️  Processing images from: {image_dir}")
        results = identifier.batch_identify_strains(image_dir)
        
        print(f"\n📊 Batch Identification Results:")
        print(f"   Processed: {results.get('processed_images', 0)} images")
        print(f"   Successful: {results.get('successful_identifications', 0)}")
        print(f"   Failed: {results.get('failed_identifications', 0)}")
        
        # Save results
        output_file = "data/strain_identification_results.json"
        identifier.save_identification_results(results, output_file)
        print(f"   💾 Results saved to: {output_file}")
        
        # Show top identification for first few images
        print(f"\n🎯 Sample Identifications:")
        for i, (image_name, result) in enumerate(list(results['results'].items())[:5]):
            if 'error' not in result and result.get('primary_identification'):
                primary = result['primary_identification']
                print(f"   {image_name}: {primary['strain_name']} "
                      f"(confidence: {primary['confidence']:.3f})")
            else:
                print(f"   {image_name}: Failed to identify")
    else:
        print(f"❌ Image directory not found: {image_dir}")
        print("   Run the strain image downloader first!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())