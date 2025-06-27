import json
import logging
from pprint import pformat

logger = logging.getLogger('router')

def log_object(obj, message="Object details:", level="info"):
    """
    Log an object in a readable format
    
    Args:
        obj: The object to log
        message: A message to prefix the logged object
        level: Logging level (info, debug, warning, error, critical)
    """
    if hasattr(obj, '__dict__'):
        # For custom objects with __dict__
        formatted = pformat(obj.__dict__)
    elif hasattr(obj, '_asdict'):
        # For namedtuples
        formatted = pformat(obj._asdict())
    else:
        try:
            # Try JSON serialization
            formatted = json.dumps(obj, indent=2, default=str)
        except:
            # Fallback to repr
            formatted = pformat(obj)
    
    log_method = getattr(logger, level.lower())
    log_method(f"{message}\n{formatted}")