#!/usr/bin/env python3
"""
GrowWiz Plant Classifier
AI-powered plant health diagnosis from images
"""

import os
import json
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import cv2
import numpy as np
from typing import Dict, List, Any, Tuple
from loguru import logger

class PlantClassifier:
    """AI model for plant health diagnosis and strain identification"""
    
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.transform = self._get_transform()
        self.classes = self._load_classes()
        self.confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.7))
        
        # Load pre-trained model if available
        model_path = os.getenv("MODEL_PATH", "./models/plant_classifier.pth")
        if os.path.exists(model_path):
            self._load_model(model_path)
        else:
            logger.warning(f"Model not found at {model_path}. Using simulation mode.")
            self.simulation_mode = True
    
    def _get_transform(self):
        """Get image preprocessing transforms"""
        return transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
    
    def _load_classes(self) -> Dict[str, Any]:
        """Load class definitions for plant conditions and strains"""
        return {
            "health_conditions": [
                "healthy",
                "nitrogen_deficiency",
                "phosphorus_deficiency",
                "potassium_deficiency",
                "calcium_deficiency",
                "magnesium_deficiency",
                "iron_deficiency",
                "light_burn",
                "nutrient_burn",
                "overwatering",
                "underwatering",
                "heat_stress",
                "cold_stress",
                "ph_imbalance",
                "pest_damage",
                "fungal_infection",
                "bacterial_infection"
            ],
            "cannabis_strains": [
                "indica_dominant",
                "sativa_dominant",
                "hybrid",
                "white_widow",
                "northern_lights",
                "og_kush",
                "blue_dream",
                "ak47",
                "purple_haze",
                "unknown_strain"
            ],
            "growth_stages": [
                "seedling",
                "vegetative",
                "pre_flower",
                "flowering",
                "harvest_ready"
            ]
        }
    
    def _load_model(self, model_path: str):
        """Load the trained classification model"""
        try:
            # Use ResNet50 as base architecture
            self.model = models.resnet50(pretrained=False)
            
            # Modify final layer for multi-class classification
            num_classes = len(self.classes["health_conditions"])
            self.model.fc = nn.Linear(self.model.fc.in_features, num_classes)
            
            # Load trained weights
            checkpoint = torch.load(model_path, map_location=self.device)
            self.model.load_state_dict(checkpoint['model_state_dict'])
            
            self.model.to(self.device)
            self.model.eval()
            
            self.simulation_mode = False
            logger.info(f"Model loaded successfully from {model_path}")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.simulation_mode = True
    
    def preprocess_image(self, image_path: str) -> torch.Tensor:
        """Preprocess image for model input"""
        try:
            # Load and convert image
            image = Image.open(image_path).convert('RGB')
            
            # Apply transforms
            tensor = self.transform(image).unsqueeze(0)
            return tensor.to(self.device)
            
        except Exception as e:
            logger.error(f"Error preprocessing image {image_path}: {e}")
            raise
    
    def extract_features(self, image_path: str) -> Dict[str, Any]:
        """Extract visual features from plant image"""
        try:
            # Load image with OpenCV for feature analysis
            img = cv2.imread(image_path)
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Calculate color statistics
            mean_color = np.mean(img_rgb, axis=(0, 1))
            
            # Detect leaf area (simplified green detection)
            hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
            green_mask = cv2.inRange(hsv, (35, 40, 40), (85, 255, 255))
            green_percentage = (np.sum(green_mask > 0) / green_mask.size) * 100
            
            # Detect brown/yellow areas (potential problems)
            yellow_mask = cv2.inRange(hsv, (20, 40, 40), (35, 255, 255))
            brown_mask = cv2.inRange(hsv, (10, 40, 40), (20, 255, 255))
            problem_percentage = ((np.sum(yellow_mask > 0) + np.sum(brown_mask > 0)) / green_mask.size) * 100
            
            features = {
                "mean_rgb": mean_color.tolist(),
                "green_percentage": round(green_percentage, 2),
                "problem_area_percentage": round(problem_percentage, 2),
                "image_size": img.shape[:2],
                "brightness": round(np.mean(cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)), 2)
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features from {image_path}: {e}")
            return {}
    
    def classify_image(self, image_path: str) -> Dict[str, Any]:
        """Main classification function - diagnose plant health from image"""
        try:
            if self.simulation_mode:
                return self._simulate_classification(image_path)
            
            # Preprocess image
            input_tensor = self.preprocess_image(image_path)
            
            # Run inference
            with torch.no_grad():
                outputs = self.model(input_tensor)
                probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
                
                # Get top predictions
                top_probs, top_indices = torch.topk(probabilities, 3)
                
                predictions = []
                for i, (prob, idx) in enumerate(zip(top_probs, top_indices)):
                    condition = self.classes["health_conditions"][idx.item()]
                    confidence = prob.item()
                    
                    predictions.append({
                        "condition": condition,
                        "confidence": round(confidence, 3),
                        "rank": i + 1
                    })
            
            # Extract visual features
            features = self.extract_features(image_path)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(predictions[0], features)
            
            result = {
                "image_path": image_path,
                "predictions": predictions,
                "primary_diagnosis": predictions[0]["condition"],
                "confidence": predictions[0]["confidence"],
                "features": features,
                "recommendations": recommendations,
                "timestamp": torch.tensor(0).item(),  # Current timestamp
                "model_version": "1.0.0"
            }
            
            logger.info(f"Classification complete: {predictions[0]['condition']} ({predictions[0]['confidence']:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Error classifying image {image_path}: {e}")
            return self._get_error_result(image_path, str(e))
    
    def _simulate_classification(self, image_path: str) -> Dict[str, Any]:
        """Simulate classification results for testing without trained model"""
        import random
        
        # Simulate realistic plant health scenarios
        conditions = [
            ("healthy", 0.85, "Plant appears healthy with good color and structure"),
            ("nitrogen_deficiency", 0.78, "Lower leaves showing yellowing, likely nitrogen deficiency"),
            ("overwatering", 0.72, "Leaves appear droopy, soil may be too wet"),
            ("light_burn", 0.69, "Upper leaves showing bleaching from intense light"),
            ("nutrient_burn", 0.75, "Leaf tips are brown, possibly from nutrient excess")
        ]
        
        # Randomly select a condition
        condition, confidence, description = random.choice(conditions)
        
        # Generate mock features
        features = {
            "mean_rgb": [random.uniform(50, 150) for _ in range(3)],
            "green_percentage": random.uniform(40, 80),
            "problem_area_percentage": random.uniform(5, 25),
            "image_size": [480, 640],
            "brightness": random.uniform(80, 180)
        }
        
        predictions = [
            {"condition": condition, "confidence": confidence, "rank": 1},
            {"condition": "healthy", "confidence": 1 - confidence, "rank": 2}
        ]
        
        recommendations = self._generate_recommendations(predictions[0], features)
        
        return {
            "image_path": image_path,
            "predictions": predictions,
            "primary_diagnosis": condition,
            "confidence": confidence,
            "features": features,
            "recommendations": recommendations,
            "timestamp": 0,
            "model_version": "simulation",
            "simulation_mode": True
        }
    
    def _generate_recommendations(self, primary_prediction: Dict, features: Dict) -> List[str]:
        """Generate actionable recommendations based on diagnosis"""
        condition = primary_prediction["condition"]
        confidence = primary_prediction["confidence"]
        
        recommendations = []
        
        # Base recommendations by condition
        condition_advice = {
            "healthy": [
                "Continue current care routine",
                "Monitor for any changes in leaf color or growth",
                "Maintain consistent watering and lighting schedule"
            ],
            "nitrogen_deficiency": [
                "Increase nitrogen-rich fertilizer",
                "Check pH levels (should be 6.0-7.0 for soil)",
                "Consider organic nitrogen sources like fish emulsion",
                "Monitor lower leaves for continued yellowing"
            ],
            "phosphorus_deficiency": [
                "Add phosphorus-rich fertilizer",
                "Check soil pH - phosphorus uptake is pH dependent",
                "Consider bone meal or rock phosphate supplements",
                "Reduce watering frequency if soil is waterlogged"
            ],
            "overwatering": [
                "Reduce watering frequency immediately",
                "Improve drainage in growing medium",
                "Allow soil to dry between waterings",
                "Check for root rot if problem persists"
            ],
            "light_burn": [
                "Increase distance between lights and plants",
                "Reduce light intensity or duration",
                "Improve ventilation to reduce heat",
                "Monitor upper leaves for further bleaching"
            ],
            "nutrient_burn": [
                "Flush growing medium with pH-balanced water",
                "Reduce nutrient concentration by 25-50%",
                "Check EC/TDS levels of nutrient solution",
                "Allow plant to recover before resuming full feeding"
            ]
        }
        
        # Get condition-specific advice
        if condition in condition_advice:
            recommendations.extend(condition_advice[condition])
        
        # Add confidence-based advice
        if confidence < 0.7:
            recommendations.append("Diagnosis confidence is moderate - monitor closely and consider getting a second opinion")
        
        # Add feature-based advice
        if features.get("problem_area_percentage", 0) > 20:
            recommendations.append("Significant problem areas detected - take immediate action")
        
        if features.get("green_percentage", 0) < 50:
            recommendations.append("Low green leaf area - plant may be severely stressed")
        
        return recommendations
    
    def _get_error_result(self, image_path: str, error_msg: str) -> Dict[str, Any]:
        """Return error result structure"""
        return {
            "image_path": image_path,
            "error": True,
            "error_message": error_msg,
            "predictions": [],
            "primary_diagnosis": "error",
            "confidence": 0.0,
            "features": {},
            "recommendations": ["Unable to analyze image - please try again with a clearer photo"],
            "timestamp": 0
        }
    
    def batch_classify(self, image_paths: List[str]) -> List[Dict[str, Any]]:
        """Classify multiple images in batch"""
        results = []
        for image_path in image_paths:
            try:
                result = self.classify_image(image_path)
                results.append(result)
            except Exception as e:
                logger.error(f"Error in batch classification for {image_path}: {e}")
                results.append(self._get_error_result(image_path, str(e)))
        
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        return {
            "simulation_mode": getattr(self, 'simulation_mode', True),
            "device": str(self.device),
            "classes": self.classes,
            "confidence_threshold": self.confidence_threshold,
            "model_loaded": self.model is not None
        }

# Example usage matching your notes
if __name__ == "__main__":
    classifier = PlantClassifier()
    
    # Test with a sample image (create a dummy image for testing)
    test_image = "test_plant.jpg"
    
    if not os.path.exists(test_image):
        # Create a dummy test image
        from PIL import Image
        import numpy as np
        
        dummy_img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        Image.fromarray(dummy_img).save(test_image)
    
    result = classifier.classify_image(test_image)
    print(json.dumps(result, indent=2))
    
    # Clean up test image
    if os.path.exists(test_image):
        os.remove(test_image)