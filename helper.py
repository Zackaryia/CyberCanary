import json
from datetime import datetime

def json_serial(obj):
    """JSON serializer for objects not serializable by default"""
    if isinstance(obj, datetime):
        return obj.isoformat()  # Converts datetime to a string format
    raise TypeError(f"Type {type(obj)} not serializable")
