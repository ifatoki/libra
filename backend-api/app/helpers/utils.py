from bson import ObjectId
from datetime import datetime

# Custom serialization function for datetime
def json_serialize(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()  # Convert datetime to ISO 8601 format
    if isinstance(obj, ObjectId):
        return str(obj)
    raise TypeError("Type not serializable")

# Custom deserialization function for datetime
def json_deserialize(obj):
    for key, value in obj.items():
        try:
            obj[key] = datetime.fromisoformat(value)  # Try to convert to datetime
        except (ValueError, TypeError):
            try:
                obj[key] = ObjectId(value)
            except:
                continue
            continue  # If it fails, keep the original value
    return obj
