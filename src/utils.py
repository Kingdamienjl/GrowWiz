"""
GrowWiz Utility Functions
Common utilities used across the project
"""

import os
import json
import time
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import re
from loguru import logger

def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure directory exists, create if it doesn't
    
    Args:
        path: Directory path
        
    Returns:
        Path object
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj

def get_timestamp() -> float:
    """Get current timestamp"""
    return time.time()

def format_timestamp(timestamp: float, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format timestamp to readable string
    
    Args:
        timestamp: Unix timestamp
        format_str: Format string
        
    Returns:
        Formatted timestamp string
    """
    return datetime.fromtimestamp(timestamp).strftime(format_str)

def get_file_hash(file_path: Union[str, Path]) -> str:
    """Get MD5 hash of file
    
    Args:
        file_path: Path to file
        
    Returns:
        MD5 hash string
    """
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.error(f"Error hashing file {file_path}: {e}")
        return ""

def safe_json_load(file_path: Union[str, Path], default: Any = None) -> Any:
    """Safely load JSON file with error handling
    
    Args:
        file_path: Path to JSON file
        default: Default value if loading fails
        
    Returns:
        Loaded JSON data or default
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Error loading JSON from {file_path}: {e}")
        return default

def safe_json_save(data: Any, file_path: Union[str, Path]) -> bool:
    """Safely save data to JSON file
    
    Args:
        data: Data to save
        file_path: Path to save file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        ensure_directory(Path(file_path).parent)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except Exception as e:
        logger.error(f"Error saving JSON to {file_path}: {e}")
        return False

def clean_text(text: str) -> str:
    """Clean and normalize text
    
    Args:
        text: Input text
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\\s+', ' ', text.strip())
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\\w\\s.,!?-]', '', text)
    
    return text

def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """Extract keywords from text
    
    Args:
        text: Input text
        min_length: Minimum keyword length
        
    Returns:
        List of keywords
    """
    if not text:
        return []
    
    # Common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
        'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
        'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you',
        'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
    }
    
    # Extract words
    words = re.findall(r'\\b\\w+\\b', text.lower())
    
    # Filter keywords
    keywords = [
        word for word in words 
        if len(word) >= min_length and word not in stop_words
    ]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for keyword in keywords:
        if keyword not in seen:
            seen.add(keyword)
            unique_keywords.append(keyword)
    
    return unique_keywords

def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate text similarity using simple word overlap
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score (0.0 to 1.0)
    """
    if not text1 or not text2:
        return 0.0
    
    words1 = set(extract_keywords(text1))
    words2 = set(extract_keywords(text2))
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0

def validate_sensor_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and clean sensor data
    
    Args:
        data: Raw sensor data
        
    Returns:
        Validated sensor data
    """
    validated = {}
    
    # Expected ranges for sensors
    ranges = {
        'temperature': (-50, 100),  # Celsius
        'humidity': (0, 100),       # Percentage
        'soil_moisture': (0, 100),  # Percentage
        'co2': (0, 5000),          # PPM
    }
    
    for key, value in data.items():
        if key == 'timestamp':
            validated[key] = value
            continue
        
        if key in ranges:
            min_val, max_val = ranges[key]
            
            # Convert to float if possible
            try:
                float_val = float(value)
                
                # Check range
                if min_val <= float_val <= max_val:
                    validated[key] = round(float_val, 2)
                else:
                    logger.warning(f"Sensor {key} value {float_val} out of range [{min_val}, {max_val}]")
                    validated[key] = None
                    
            except (ValueError, TypeError):
                logger.warning(f"Invalid sensor {key} value: {value}")
                validated[key] = None
        else:
            validated[key] = value
    
    return validated

def format_sensor_data(data: Dict[str, Any]) -> str:
    """Format sensor data for display
    
    Args:
        data: Sensor data
        
    Returns:
        Formatted string
    """
    if not data:
        return "No sensor data"
    
    lines = []
    
    if 'timestamp' in data:
        lines.append(f"Time: {format_timestamp(data['timestamp'])}")
    
    if 'temperature' in data and data['temperature'] is not None:
        lines.append(f"Temperature: {data['temperature']}°C")
    
    if 'humidity' in data and data['humidity'] is not None:
        lines.append(f"Humidity: {data['humidity']}%")
    
    if 'soil_moisture' in data and data['soil_moisture'] is not None:
        lines.append(f"Soil Moisture: {data['soil_moisture']}%")
    
    if 'co2' in data and data['co2'] is not None:
        lines.append(f"CO2: {data['co2']} ppm")
    
    return "\\n".join(lines)

def get_file_size(file_path: Union[str, Path]) -> int:
    """Get file size in bytes
    
    Args:
        file_path: Path to file
        
    Returns:
        File size in bytes, 0 if file doesn't exist
    """
    try:
        return os.path.getsize(file_path)
    except OSError:
        return 0

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def retry_async(max_retries: int = 3, delay: float = 1.0):
    """Decorator for retrying async functions
    
    Args:
        max_retries: Maximum number of retries
        delay: Delay between retries in seconds
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}")
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}")
            
            raise last_exception
        
        return wrapper
    return decorator

def retry_sync(max_retries: int = 3, delay: float = 1.0):
    """Decorator for retrying sync functions
    
    Args:
        max_retries: Maximum number of retries
        delay: Delay between retries in seconds
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}")
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}")
            
            raise last_exception
        
        return wrapper
    return decorator

def is_raspberry_pi() -> bool:
    """Check if running on Raspberry Pi
    
    Returns:
        True if running on Raspberry Pi
    """
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            return 'BCM' in cpuinfo or 'ARM' in cpuinfo
    except:
        return False

def get_system_info() -> Dict[str, Any]:
    """Get system information
    
    Returns:
        Dictionary with system info
    """
    import platform
    import psutil
    
    info = {
        'platform': platform.system(),
        'platform_release': platform.release(),
        'platform_version': platform.version(),
        'architecture': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
        'is_raspberry_pi': is_raspberry_pi(),
        'cpu_count': psutil.cpu_count(),
        'memory_total': psutil.virtual_memory().total,
        'memory_available': psutil.virtual_memory().available,
        'disk_usage': psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:\\\\').percent
    }
    
    return info

def create_backup_filename(original_path: Union[str, Path], suffix: str = None) -> str:
    """Create backup filename with timestamp
    
    Args:
        original_path: Original file path
        suffix: Optional suffix
        
    Returns:
        Backup filename
    """
    path_obj = Path(original_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if suffix:
        backup_name = f"{path_obj.stem}_{timestamp}_{suffix}{path_obj.suffix}"
    else:
        backup_name = f"{path_obj.stem}_{timestamp}{path_obj.suffix}"
    
    return str(path_obj.parent / backup_name)

def parse_duration(duration_str: str) -> float:
    """Parse duration string to seconds
    
    Args:
        duration_str: Duration string (e.g., '1h', '30m', '45s')
        
    Returns:
        Duration in seconds
    """
    if not duration_str:
        return 0.0
    
    # Remove spaces
    duration_str = duration_str.replace(' ', '').lower()
    
    # Parse different units
    multipliers = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400,
        'w': 604800
    }
    
    total_seconds = 0.0
    
    # Find all number-unit pairs
    pattern = r'(\\d+(?:\\.\\d+)?)([smhdw])'
    matches = re.findall(pattern, duration_str)
    
    for value_str, unit in matches:
        value = float(value_str)
        multiplier = multipliers.get(unit, 1)
        total_seconds += value * multiplier
    
    return total_seconds

class RateLimiter:
    """Simple rate limiter"""
    
    def __init__(self, max_calls: int, time_window: float):
        """Initialize rate limiter
        
        Args:
            max_calls: Maximum calls allowed
            time_window: Time window in seconds
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def is_allowed(self) -> bool:
        """Check if call is allowed
        
        Returns:
            True if call is allowed
        """
        now = time.time()
        
        # Remove old calls
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        # Check if we can make another call
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        
        return False
    
    def time_until_allowed(self) -> float:
        """Get time until next call is allowed
        
        Returns:
            Seconds until next call is allowed
        """
        if len(self.calls) < self.max_calls:
            return 0.0
        
        oldest_call = min(self.calls)
        return self.time_window - (time.time() - oldest_call)

# Example usage and tests
if __name__ == "__main__":
    print("GrowWiz Utilities Test")
    print("=" * 30)
    
    # Test timestamp functions
    now = get_timestamp()
    print(f"Current timestamp: {now}")
    print(f"Formatted: {format_timestamp(now)}")
    
    # Test text processing
    sample_text = "This is a sample text about cannabis growing and cultivation techniques."
    keywords = extract_keywords(sample_text)
    print(f"Keywords: {keywords}")
    
    # Test sensor data validation
    sensor_data = {
        'temperature': 25.5,
        'humidity': 60.0,
        'soil_moisture': 45.0,
        'co2': 800,
        'timestamp': now
    }
    
    validated = validate_sensor_data(sensor_data)
    print(f"Validated sensor data: {validated}")
    print(f"Formatted: {format_sensor_data(validated)}")
    
    # Test system info
    sys_info = get_system_info()
    print(f"System info: {sys_info}")
    
    # Test rate limiter
    limiter = RateLimiter(5, 60)  # 5 calls per minute
    print(f"Rate limiter test: {limiter.is_allowed()}")
    
    print("Utilities test completed!")