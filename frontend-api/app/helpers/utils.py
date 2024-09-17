import json
from bson import ObjectId
from datetime import datetime
from app import mongo

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

# Handle all frontend events
def handle_events(message):
    data = json.loads(message['data'], object_hook=json_deserialize)
    if data['event'] == 'book_added':
        # Process the event and update MongoDB
        book = data
        del book['event']
        book['available'] = True
        mongo.db.books.insert_one(book)
        print("book added on frontend.")
    elif data['event'] == 'book_removed':
        # Process the event and update MongoDB
        book = data
        del book['event']
        mongo.db.books.delete_one({"_id": book['_id']})
        print("Borrow record registered on backend.")