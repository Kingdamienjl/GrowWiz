"""
Grow Calendar and Management API
Flask blueprint for grow tracking, scheduling, and calendar functionality
"""

from flask import Blueprint, request, jsonify, render_template
from datetime import datetime, timedelta
import json
import logging
import os
from typing import Dict, Any, List
import calendar

from .grow_management import GrowManagementSystem, GrowType, GrowPhase

logger = logging.getLogger(__name__)

# Create blueprint
grow_calendar_bp = Blueprint('grow_calendar', __name__, url_prefix='/api/grow')

# Initialize grow management system
grow_manager = GrowManagementSystem()

# Calendar notes storage
NOTES_FILE = os.path.join('data', 'calendar_notes.json')

def load_notes():
    """Load calendar notes from file"""
    try:
        if os.path.exists(NOTES_FILE):
            with open(NOTES_FILE, 'r') as f:
                return json.load(f)
        return {"notes": {}, "sessions": {}, "last_updated": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Error loading notes: {e}")
        return {"notes": {}, "sessions": {}, "last_updated": datetime.now().isoformat()}

def save_notes(notes_data):
    """Save calendar notes to file"""
    try:
        os.makedirs(os.path.dirname(NOTES_FILE), exist_ok=True)
        notes_data["last_updated"] = datetime.now().isoformat()
        with open(NOTES_FILE, 'w') as f:
            json.dump(notes_data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving notes: {e}")
        return False

@grow_calendar_bp.route('/calendar/<int:year>/<int:month>')
def get_calendar_data(year: int, month: int):
    """Get calendar data for a specific month"""
    try:
        # Validate date
        if month < 1 or month > 12:
            return jsonify({'success': False, 'error': 'Invalid month'}), 400
        
        # Get calendar info
        cal = calendar.Calendar(firstweekday=6)  # Start with Sunday
        month_days = list(cal.itermonthdates(year, month))
        
        # Load notes
        notes_data = load_notes()
        
        # Build calendar structure
        calendar_data = {
            'year': year,
            'month': month,
            'month_name': calendar.month_name[month],
            'days_in_month': calendar.monthrange(year, month)[1],
            'first_weekday': calendar.monthrange(year, month)[0],
            'weeks': []
        }
        
        # Group days into weeks
        weeks = []
        current_week = []
        
        for date in month_days:
            day_key = date.strftime('%Y-%m-%d')
            day_data = {
                'date': date.strftime('%Y-%m-%d'),
                'day': date.day,
                'is_current_month': date.month == month,
                'is_today': date == datetime.now().date(),
                'notes': notes_data['notes'].get(day_key, ''),
                'has_session': day_key in notes_data.get('sessions', {}),
                'session_info': notes_data.get('sessions', {}).get(day_key, {})
            }
            
            current_week.append(day_data)
            
            if len(current_week) == 7:
                weeks.append(current_week)
                current_week = []
        
        if current_week:
            weeks.append(current_week)
        
        calendar_data['weeks'] = weeks
        
        return jsonify({
            'success': True,
            'calendar': calendar_data
        })
        
    except Exception as e:
        logger.error(f"Error getting calendar data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grow_calendar_bp.route('/notes', methods=['POST'])
def save_day_note():
    """Save a note for a specific day"""
    try:
        data = request.get_json()
        date = data.get('date')
        note = data.get('note', '')
        
        if not date:
            return jsonify({'success': False, 'error': 'Date is required'}), 400
        
        # Validate date format
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Load, update, and save notes
        notes_data = load_notes()
        notes_data['notes'][date] = note
        
        if save_notes(notes_data):
            return jsonify({
                'success': True,
                'message': 'Note saved successfully',
                'date': date,
                'note': note
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to save note'}), 500
            
    except Exception as e:
        logger.error(f"Error saving note: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grow_calendar_bp.route('/notes/<date>')
def get_day_note(date: str):
    """Get note for a specific day"""
    try:
        # Validate date format
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        notes_data = load_notes()
        note = notes_data['notes'].get(date, '')
        
        return jsonify({
            'success': True,
            'date': date,
            'note': note
        })
        
    except Exception as e:
        logger.error(f"Error getting note: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grow_calendar_bp.route('/prerequisites/<grow_type>')
def get_prerequisites(grow_type: str):
    """Get prerequisites for a specific grow type"""
    try:
        grow_type_enum = GrowType(grow_type.lower())
        prerequisites = grow_manager.get_prerequisites(grow_type_enum)
        
        return jsonify({
            'success': True,
            'grow_type': grow_type,
            'prerequisites': prerequisites
        })
    except ValueError:
        return jsonify({
            'success': False,
            'error': f'Invalid grow type: {grow_type}. Valid types: {[gt.value for gt in GrowType]}'
        }), 400
    except Exception as e:
        logger.error(f"Error getting prerequisites: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grow_calendar_bp.route('/products/<grow_type>')
def get_product_list(grow_type: str):
    """Get product list for a specific grow type"""
    try:
        grow_type_enum = GrowType(grow_type.lower())
        budget_level = request.args.get('budget', 'medium')
        
        products = grow_manager.get_product_list(grow_type_enum, budget_level)
        
        return jsonify({
            'success': True,
            'grow_type': grow_type,
            'budget_level': budget_level,
            'products': products
        })
    except ValueError:
        return jsonify({
            'success': False,
            'error': f'Invalid grow type: {grow_type}. Valid types: {[gt.value for gt in GrowType]}'
        }), 400
    except Exception as e:
        logger.error(f"Error getting product list: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grow_calendar_bp.route('/chemicals/<phase>')
def get_chemical_guide(phase: str):
    """Get chemical guide for a specific grow phase"""
    try:
        phase_enum = GrowPhase(phase.lower())
        guide = grow_manager.get_chemical_guide(phase_enum)
        
        return jsonify({
            'success': True,
            'phase': phase,
            'guide': guide
        })
    except ValueError:
        return jsonify({
            'success': False,
            'error': f'Invalid phase: {phase}. Valid phases: {[gp.value for gp in GrowPhase]}'
        }), 400
    except Exception as e:
        logger.error(f"Error getting chemical guide: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grow_calendar_bp.route('/schedule/<grow_type>/<int:week>')
def get_weekly_schedule(grow_type: str, week: int):
    """Get weekly schedule for specific grow type and week"""
    try:
        grow_type_enum = GrowType(grow_type.lower())
        schedule = grow_manager.get_weekly_schedule(grow_type_enum, week)
        
        if schedule:
            return jsonify({
                'success': True,
                'grow_type': grow_type,
                'week': week,
                'schedule': {
                    'week': schedule.week,
                    'phase': schedule.phase.value,
                    'light_schedule': schedule.light_schedule,
                    'temperature_day': schedule.temperature_day,
                    'temperature_night': schedule.temperature_night,
                    'humidity': schedule.humidity,
                    'nutrients': schedule.nutrients,
                    'watering_frequency': schedule.watering_frequency,
                    'tasks': schedule.tasks,
                    'notes': schedule.notes
                }
            })
        else:
            # Return detailed germination schedule for week 1 if not found
            if week == 1:
                return jsonify({
                    'success': True,
                    'grow_type': grow_type,
                    'week': week,
                    'schedule': {
                        'week': 1,
                        'phase': 'germination',
                        'light_schedule': '18/6 (18 hours on, 6 hours off)',
                        'temperature_day': '75-80°F (24-27°C)',
                        'temperature_night': '65-70°F (18-21°C)',
                        'humidity': '70-80%',
                        'nutrients': 'None - use pH balanced water only',
                        'watering_frequency': 'Keep growing medium moist but not soaked',
                        'tasks': [
                            'Soak seeds in pH 6.0 water for 12-24 hours',
                            'Place seeds in growing medium (rockwool, peat pellets, or soil)',
                            'Maintain consistent temperature and humidity',
                            'Monitor for taproot emergence (24-72 hours)',
                            'Once sprouted, provide gentle light (T5 fluorescent or LED at 24+ inches)',
                            'Keep humidity dome on seedlings',
                            'Check pH of water (should be 6.0-6.5 for soil, 5.5-6.0 for hydro)'
                        ],
                        'notes': 'Germination is critical - maintain stable environment. Seeds typically sprout within 2-7 days. Do not overwater or overfeed at this stage.'
                    }
                })
            
            return jsonify({
                'success': False,
                'error': f'No schedule found for {grow_type} week {week}'
            }), 404
    except ValueError:
        return jsonify({
            'success': False,
            'error': f'Invalid grow type: {grow_type}. Valid types: {[gt.value for gt in GrowType]}'
        }), 400
    except Exception as e:
        logger.error(f"Error getting weekly schedule: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grow_calendar_bp.route('/sessions', methods=['GET'])
def get_active_sessions():
    """Get all active grow sessions"""
    try:
        sessions = grow_manager.get_active_sessions()
        session_data = []
        
        for session in sessions:
            session_data.append({
                'id': session.id,
                'strain_name': session.strain_name,
                'grow_type': session.grow_type.value,
                'start_date': session.start_date.isoformat(),
                'current_week': session.current_week,
                'current_phase': session.current_phase.value,
                'expected_harvest': session.expected_harvest.isoformat(),
                'days_remaining': (session.expected_harvest - datetime.now()).days,
                'notes': session.notes,
                'active': session.active
            })
        
        return jsonify({
            'success': True,
            'sessions': session_data
        })
    except Exception as e:
        logger.error(f"Error getting active sessions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grow_calendar_bp.route('/sessions', methods=['POST'])
def create_grow_session():
    """Create new grow session"""
    try:
        data = request.get_json()
        strain_name = data.get('strain_name')
        grow_type = data.get('grow_type')
        
        if not strain_name or not grow_type:
            return jsonify({
                'success': False,
                'error': 'strain_name and grow_type are required'
            }), 400
        
        grow_type_enum = GrowType(grow_type.lower())
        session = grow_manager.create_grow_session(strain_name, grow_type_enum)
        
        return jsonify({
            'success': True,
            'session': {
                'id': session.id,
                'strain_name': session.strain_name,
                'grow_type': session.grow_type.value,
                'start_date': session.start_date.isoformat(),
                'current_week': session.current_week,
                'current_phase': session.current_phase.value,
                'expected_harvest': session.expected_harvest.isoformat(),
                'notes': session.notes,
                'active': session.active
            }
        })
    except ValueError:
        return jsonify({
            'success': False,
            'error': f'Invalid grow type: {grow_type}. Valid types: {[gt.value for gt in GrowType]}'
        }), 400
    except Exception as e:
        logger.error(f"Error creating grow session: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grow_calendar_bp.route('/sessions/<session_id>/week', methods=['PUT'])
def update_session_week(session_id: str):
    """Update grow session week"""
    try:
        data = request.get_json()
        new_week = data.get('week')
        
        if not new_week:
            return jsonify({
                'success': False,
                'error': 'week is required'
            }), 400
        
        success = grow_manager.update_session_week(session_id, new_week)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Session {session_id} updated to week {new_week}'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Session {session_id} not found'
            }), 404
    except Exception as e:
        logger.error(f"Error updating session week: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grow_calendar_bp.route('/sessions/<session_id>/export')
def export_session_data(session_id: str):
    """Export grow session data"""
    try:
        session_data = grow_manager.export_session_data(session_id)
        
        if session_data:
            return jsonify({
                'success': True,
                'session_data': session_data
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Session {session_id} not found'
            }), 404
    except Exception as e:
        logger.error(f"Error exporting session data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grow_calendar_bp.route('/calendar/<grow_type>')
def get_calendar_data(grow_type: str):
    """Get calendar data for grow type"""
    try:
        grow_type_enum = GrowType(grow_type.lower())
        schedules = grow_manager.grow_schedules.get(grow_type_enum, [])
        
        calendar_events = []
        for schedule in schedules:
            calendar_events.append({
                'week': schedule.week,
                'phase': schedule.phase.value,
                'title': f'Week {schedule.week}: {schedule.phase.value.title()}',
                'tasks': schedule.tasks,
                'notes': schedule.notes,
                'environmental': {
                    'light_schedule': schedule.light_schedule,
                    'temperature_day': schedule.temperature_day,
                    'temperature_night': schedule.temperature_night,
                    'humidity': schedule.humidity
                },
                'nutrients': schedule.nutrients,
                'watering': schedule.watering_frequency
            })
        
        return jsonify({
            'success': True,
            'grow_type': grow_type,
            'calendar_events': calendar_events
        })
    except ValueError:
        return jsonify({
            'success': False,
            'error': f'Invalid grow type: {grow_type}. Valid types: {[gt.value for gt in GrowType]}'
        }), 400
    except Exception as e:
        logger.error(f"Error getting calendar data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grow_calendar_bp.route('/grow-types')
def get_grow_types():
    """Get available grow types"""
    try:
        return jsonify({
            'success': True,
            'grow_types': [
                {
                    'value': gt.value,
                    'name': gt.value.replace('_', ' ').title(),
                    'description': _get_grow_type_description(gt)
                }
                for gt in GrowType
            ]
        })
    except Exception as e:
        logger.error(f"Error getting grow types: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@grow_calendar_bp.route('/phases')
def get_grow_phases():
    """Get available grow phases"""
    try:
        return jsonify({
            'success': True,
            'phases': [
                {
                    'value': gp.value,
                    'name': gp.value.replace('_', ' ').title(),
                    'description': _get_phase_description(gp)
                }
                for gp in GrowPhase
            ]
        })
    except Exception as e:
        logger.error(f"Error getting grow phases: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def _get_grow_type_description(grow_type: GrowType) -> str:
    """Get description for grow type"""
    descriptions = {
        GrowType.AUTOFLOWER: "Automatic flowering plants that don't require light schedule changes (10-12 weeks)",
        GrowType.PHOTOPERIOD_SEED: "Traditional photoperiod plants grown from seed (16-20 weeks)",
        GrowType.PHOTOPERIOD_CLONE: "Photoperiod plants grown from clones (12-16 weeks)",
        GrowType.FEMINIZED_SEED: "Feminized photoperiod seeds (16-18 weeks)"
    }
    return descriptions.get(grow_type, "Unknown grow type")

def _get_phase_description(phase: GrowPhase) -> str:
    """Get description for grow phase"""
    descriptions = {
        GrowPhase.GERMINATION: "Seed sprouting and initial root development",
        GrowPhase.SEEDLING: "First true leaves and early growth",
        GrowPhase.VEGETATIVE: "Rapid growth and leaf development",
        GrowPhase.PRE_FLOWER: "Transition to flowering, sex determination",
        GrowPhase.FLOWERING: "Bud development and maturation",
        GrowPhase.HARVEST: "Cutting and initial processing",
        GrowPhase.CURING: "Drying and curing for final product"
    }
    return descriptions.get(phase, "Unknown phase")