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

# Handle all backend events
def handle_events(message):
    data = json.loads(message['data'], object_hook=json_deserialize)
    if data['event'] == 'user_enrolled':
        # Process the event and update MongoDB
        user = data
        del user['event']
        mongo.db.users.insert_one(user)
        print("user enrolled on backend.")
    elif data['event'] == 'book_borrowed':
        # Process the event and update MongoDB
        borrow_record = data
        del borrow_record['event']
        mongo.db.borrow_records.insert_one(borrow_record)
        mongo.db.books.update_one(
			{"_id": borrow_record['book_id']},
			{"$set": {
				"available": False,
				"available_on": borrow_record['borrowed_until']
			}}
		)
        print("Borrow record registered on backend.")