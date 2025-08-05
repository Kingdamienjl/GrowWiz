"""
Unit tests for GrowWiz plant classifier module
"""

import pytest
import sys
import os
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import numpy as np

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from plant_classifier import PlantClassifier

class TestPlantClassifier:
    """Test cases for PlantClassifier class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.classifier = PlantClassifier()
        
        # Create a test image
        self.test_image = self._create_test_image()
    
    def teardown_method(self):
        """Clean up after tests"""
        if hasattr(self.test_image, 'close'):
            self.test_image.close()
    
    def _create_test_image(self):
        """Create a test image file"""
        # Create a simple green image (simulating a plant)
        img = Image.new('RGB', (224, 224), color='green')
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        img.save(temp_file.name)
        temp_file.close()
        
        return temp_file.name
    
    def test_initialization(self):
        """Test classifier initialization"""
        assert self.classifier is not None
        assert hasattr(self.classifier, 'model_name')
        assert hasattr(self.classifier, 'simulation_mode')
        assert hasattr(self.classifier, 'confidence_threshold')
    
    def test_simulation_mode_default(self):
        """Test that simulation mode is enabled by default"""
        assert self.classifier.simulation_mode is True
    
    def test_load_config(self):
        """Test configuration loading"""
        config = self.classifier._load_config()
        
        assert isinstance(config, dict)
        assert 'model_name' in config
        assert 'confidence_threshold' in config
        assert 'max_image_size' in config
    
    def test_preprocess_image(self):
        """Test image preprocessing"""
        processed = self.classifier._preprocess_image(self.test_image)
        
        assert processed is not None
        assert isinstance(processed, np.ndarray)
        assert processed.shape == (224, 224, 3)  # Expected input shape
        assert processed.dtype == np.float32
        assert 0 <= processed.min() and processed.max() <= 1  # Normalized
    
    def test_preprocess_image_invalid_path(self):
        """Test preprocessing with invalid image path"""
        with pytest.raises(Exception):
            self.classifier._preprocess_image('nonexistent_image.jpg')
    
    def test_extract_features(self):
        """Test feature extraction from image"""
        features = self.classifier._extract_features(self.test_image)
        
        assert isinstance(features, dict)
        
        # Check required features
        required_features = [
            'brightness', 'contrast', 'green_percentage', 
            'problem_area_percentage', 'color_variance'
        ]
        
        for feature in required_features:
            assert feature in features
            assert isinstance(features[feature], (int, float))
        
        # Check feature ranges
        assert 0 <= features['brightness'] <= 255
        assert 0 <= features['green_percentage'] <= 100
        assert 0 <= features['problem_area_percentage'] <= 100
    
    def test_classify_image_simulation(self):
        """Test image classification in simulation mode"""
        result = self.classifier.classify_image(self.test_image)
        
        assert isinstance(result, dict)
        
        # Check required fields
        required_fields = [
            'image_path', 'primary_diagnosis', 'confidence', 
            'predictions', 'recommendations', 'features', 'simulation_mode'
        ]
        
        for field in required_fields:
            assert field in result
        
        # Check data types
        assert isinstance(result['image_path'], str)
        assert isinstance(result['primary_diagnosis'], str)
        assert isinstance(result['confidence'], (int, float))
        assert isinstance(result['predictions'], list)
        assert isinstance(result['recommendations'], list)
        assert isinstance(result['features'], dict)
        assert result['simulation_mode'] is True
        
        # Check confidence range
        assert 0 <= result['confidence'] <= 1
    
    def test_classify_image_invalid_path(self):
        """Test classification with invalid image path"""
        result = self.classifier.classify_image('nonexistent_image.jpg')
        
        assert result['error'] is True
        assert 'error_message' in result
    
    def test_get_recommendations(self):
        """Test recommendation generation"""
        # Test with healthy plant
        healthy_features = {
            'green_percentage': 80,
            'problem_area_percentage': 5,
            'brightness': 120
        }
        
        recommendations = self.classifier._get_recommendations('healthy', healthy_features)
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Test with diseased plant
        diseased_features = {
            'green_percentage': 40,
            'problem_area_percentage': 30,
            'brightness': 80
        }
        
        recommendations = self.classifier._get_recommendations('nutrient_deficiency', diseased_features)
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
    
    def test_simulate_classification(self):
        """Test classification simulation"""
        result = self.classifier._simulate_classification(self.test_image)
        
        assert isinstance(result, dict)
        assert 'primary_diagnosis' in result
        assert 'confidence' in result
        assert 'predictions' in result
        
        # Check that predictions are properly formatted
        for prediction in result['predictions']:
            assert 'condition' in prediction
            assert 'confidence' in prediction
            assert isinstance(prediction['confidence'], (int, float))
            assert 0 <= prediction['confidence'] <= 1
    
    @patch('plant_classifier.torch')
    @patch('plant_classifier.torchvision')
    def test_load_model_mock(self, mock_torchvision, mock_torch):
        """Test model loading with mocked PyTorch"""
        # Mock model
        mock_model = Mock()
        mock_torchvision.models.resnet50.return_value = mock_model
        
        # Create classifier in hardware mode
        classifier = PlantClassifier()
        classifier.simulation_mode = False
        
        # Test model loading
        model = classifier._load_model()
        
        assert model is not None
        mock_torchvision.models.resnet50.assert_called_once()
    
    def test_color_analysis(self):
        """Test color analysis functionality"""
        # Create test image with specific colors
        img = Image.new('RGB', (100, 100))
        pixels = img.load()
        
        # Fill with green (healthy plant color)
        for i in range(100):
            for j in range(100):
                pixels[i, j] = (0, 255, 0)  # Pure green
        
        # Save test image
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        img.save(temp_file.name)
        temp_file.close()
        
        try:
            features = self.classifier._extract_features(temp_file.name)
            
            # Should detect high green percentage
            assert features['green_percentage'] > 50
            assert features['problem_area_percentage'] < 50
            
        finally:
            os.unlink(temp_file.name)
    
    def test_batch_classification(self):
        """Test batch classification of multiple images"""
        # Create multiple test images
        image_paths = []
        for i in range(3):
            img = Image.new('RGB', (224, 224), color=('red', 'green', 'blue')[i])
            temp_file = tempfile.NamedTemporaryFile(suffix=f'_test_{i}.jpg', delete=False)
            img.save(temp_file.name)
            temp_file.close()
            image_paths.append(temp_file.name)
        
        try:
            results = []
            for path in image_paths:
                result = self.classifier.classify_image(path)
                results.append(result)
            
            # All results should be valid
            assert len(results) == 3
            for result in results:
                assert isinstance(result, dict)
                assert 'primary_diagnosis' in result
                
        finally:
            # Clean up
            for path in image_paths:
                if os.path.exists(path):
                    os.unlink(path)
    
    def test_confidence_threshold(self):
        """Test confidence threshold functionality"""
        # Test with different thresholds
        classifier_high = PlantClassifier()
        classifier_high.confidence_threshold = 0.9
        
        classifier_low = PlantClassifier()
        classifier_low.confidence_threshold = 0.1
        
        # Both should work in simulation mode
        result_high = classifier_high.classify_image(self.test_image)
        result_low = classifier_low.classify_image(self.test_image)
        
        assert isinstance(result_high, dict)
        assert isinstance(result_low, dict)
    
    def test_error_handling(self):
        """Test error handling in classification"""
        # Test with None input
        result = self.classifier.classify_image(None)
        assert result['error'] is True
        
        # Test with empty string
        result = self.classifier.classify_image('')
        assert result['error'] is True
        
        # Test with directory instead of file
        temp_dir = tempfile.mkdtemp()
        try:
            result = self.classifier.classify_image(temp_dir)
            assert result['error'] is True
        finally:
            os.rmdir(temp_dir)
    
    def test_feature_extraction_edge_cases(self):
        """Test feature extraction with edge cases"""
        # Create black image
        black_img = Image.new('RGB', (100, 100), color='black')
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        black_img.save(temp_file.name)
        temp_file.close()
        
        try:
            features = self.classifier._extract_features(temp_file.name)
            
            # Should handle black image gracefully
            assert isinstance(features, dict)
            assert features['brightness'] < 50  # Should be low
            assert features['green_percentage'] < 10  # Should be very low
            
        finally:
            os.unlink(temp_file.name)
    
    def test_model_predictions_format(self):
        """Test that model predictions follow expected format"""
        result = self.classifier.classify_image(self.test_image)
        
        if not result.get('error'):
            predictions = result['predictions']
            
            # Should have multiple predictions
            assert len(predictions) > 0
            
            # Each prediction should have required fields
            for pred in predictions:
                assert 'condition' in pred
                assert 'confidence' in pred
                assert isinstance(pred['condition'], str)
                assert isinstance(pred['confidence'], (int, float))
                assert 0 <= pred['confidence'] <= 1
            
            # Predictions should be sorted by confidence (descending)
            confidences = [pred['confidence'] for pred in predictions]
            assert confidences == sorted(confidences, reverse=True)
    
    def test_recommendations_relevance(self):
        """Test that recommendations are relevant to diagnosis"""
        # Test different conditions
        conditions = ['healthy', 'nutrient_deficiency', 'overwatering', 'pest_damage']
        
        for condition in conditions:
            features = {
                'green_percentage': 60,
                'problem_area_percentage': 20,
                'brightness': 100
            }
            
            recommendations = self.classifier._get_recommendations(condition, features)
            
            assert isinstance(recommendations, list)
            assert len(recommendations) > 0
            
            # Recommendations should be strings
            for rec in recommendations:
                assert isinstance(rec, str)
                assert len(rec) > 0

class TestPlantClassifierIntegration:
    """Integration tests for plant classifier"""
    
    def test_full_classification_pipeline(self):
        """Test the complete classification pipeline"""
        classifier = PlantClassifier()
        
        # Create test image
        img = Image.new('RGB', (300, 300), color='green')
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        img.save(temp_file.name)
        temp_file.close()
        
        try:
            # Run full classification
            result = classifier.classify_image(temp_file.name)
            
            # Verify complete result structure
            assert isinstance(result, dict)
            
            if not result.get('error'):
                # Check all expected components
                assert 'image_path' in result
                assert 'primary_diagnosis' in result
                assert 'confidence' in result
                assert 'predictions' in result
                assert 'recommendations' in result
                assert 'features' in result
                
                # Verify data integrity
                assert result['image_path'] == temp_file.name
                assert isinstance(result['primary_diagnosis'], str)
                assert 0 <= result['confidence'] <= 1
                assert len(result['predictions']) > 0
                assert len(result['recommendations']) > 0
                assert isinstance(result['features'], dict)
            
        finally:
            os.unlink(temp_file.name)
    
    def test_performance(self):
        """Test classification performance"""
        import time
        
        classifier = PlantClassifier()
        
        # Create test image
        img = Image.new('RGB', (224, 224), color='green')
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        img.save(temp_file.name)
        temp_file.close()
        
        try:
            # Measure classification time
            start_time = time.time()
            result = classifier.classify_image(temp_file.name)
            end_time = time.time()
            
            # Should complete in reasonable time (< 10 seconds in simulation)
            assert (end_time - start_time) < 10.0
            assert not result.get('error')
            
        finally:
            os.unlink(temp_file.name)

if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])