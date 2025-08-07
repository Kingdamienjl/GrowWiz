#!/usr/bin/env python3
"""
GrowWiz Strain Identification API
Flask API endpoints for strain identification from images
"""

import os
import json
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from PIL import Image
import tempfile
from pathlib import Path
import uuid
from loguru import logger

# Import our strain identifier
from .strain_identifier import StrainIdentifier

# Create blueprint
strain_id_bp = Blueprint('strain_identification', __name__)

# Global strain identifier instance
strain_identifier = None

def init_strain_identifier():
    """Initialize the strain identifier"""
    global strain_identifier
    if strain_identifier is None:
        try:
            strain_identifier = StrainIdentifier()
            logger.info("Strain identifier initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize strain identifier: {e}")
            strain_identifier = None
    return strain_identifier

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@strain_id_bp.route('/api/strain/identify', methods=['POST'])
def identify_strain_from_image():
    """
    Identify strain from uploaded image
    
    Expected: multipart/form-data with 'image' file
    Returns: JSON with strain identification results
    """
    try:
        # Initialize identifier if needed
        identifier = init_strain_identifier()
        if identifier is None:
            return jsonify({
                'success': False,
                'error': 'Strain identification system not available'
            }), 500
        
        # Check if image file is present
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image file provided'
            }), 400
        
        file = request.files['image']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Check file type
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Invalid file type. Allowed: PNG, JPG, JPEG, GIF, WEBP, BMP'
            }), 400
        
        # Get optional parameters
        top_k = request.form.get('top_k', 5, type=int)
        top_k = min(max(top_k, 1), 20)  # Limit between 1-20
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            temp_path = temp_file.name
            
            try:
                # Save and process image
                file.save(temp_path)
                
                # Validate image
                try:
                    with Image.open(temp_path) as img:
                        # Convert to RGB if needed
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                            img.save(temp_path, 'JPEG')
                except Exception as e:
                    return jsonify({
                        'success': False,
                        'error': f'Invalid image file: {str(e)}'
                    }), 400
                
                # Perform strain identification
                result = identifier.identify_strain(temp_path, top_k=top_k)
                
                if 'error' in result:
                    return jsonify({
                        'success': False,
                        'error': result['error']
                    }), 500
                
                # Format response
                response_data = {
                    'success': True,
                    'identification': {
                        'primary_match': result.get('primary_identification'),
                        'top_matches': result.get('top_matches', []),
                        'total_compared': result.get('total_strains_compared', 0),
                        'method': result.get('identification_method', 'unknown'),
                        'model_version': result.get('model_version', 'unknown')
                    },
                    'visual_analysis': {
                        'features_extracted': bool(result.get('visual_features')),
                        'color_analysis': result.get('visual_features', {}).get('green_percentage') is not None,
                        'texture_analysis': result.get('visual_features', {}).get('texture_contrast') is not None,
                        'shape_analysis': result.get('visual_features', {}).get('circularity') is not None
                    }
                }
                
                return jsonify(response_data)
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except:
                    pass
    
    except Exception as e:
        logger.error(f"Error in strain identification API: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error during strain identification'
        }), 500

@strain_id_bp.route('/api/strain/identify/status', methods=['GET'])
def get_identification_status():
    """Get status of strain identification system"""
    try:
        identifier = init_strain_identifier()
        
        if identifier is None:
            return jsonify({
                'available': False,
                'error': 'Strain identification system not initialized'
            }), 200
        
        return jsonify({
            'available': True,
            'total_strains': len(identifier.strain_classes) if hasattr(identifier, 'strain_classes') else 635,
            'simulation_mode': getattr(identifier, 'simulation_mode', True),
            'model_version': '1.0.0_simulation',
            'supported_formats': ['PNG', 'JPG', 'JPEG', 'GIF', 'WEBP', 'BMP'],
            'max_top_results': 20
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting identification status: {e}")
        return jsonify({
            'available': False,
            'error': 'Error checking system status'
        }), 200



# Error handlers
@strain_id_bp.errorhandler(413)
def too_large(e):
    return jsonify({
        'success': False,
        'error': 'File too large. Maximum size allowed is 16MB.'
    }), 413

@strain_id_bp.errorhandler(400)
def bad_request(e):
    return jsonify({
        'success': False,
        'error': 'Bad request'
    }), 400

@strain_id_bp.errorhandler(500)
def internal_error(e):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500