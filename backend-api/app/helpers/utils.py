"""
Utility module for custom JSON serialization, deserialization,
and handling backend events related to users and books.
"""

import json
from datetime import datetime
from functools import reduce
from validator_collection import checkers

from app import mongo
from bson import ObjectId, errors


def json_serialize(obj):
    """
    Serialize datetime or ObjectId to a string.
    Convert datetime to ISO 8601 format or ObjectId to string.
    Raise TypeError for unsupported types.
    """

    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, ObjectId):
        return str(obj)
    raise TypeError("Type not serializable")


# Custom deserialization function for datetime
def json_deserialize(obj):
    """
    Deserializes JSON object fields to datetime or ObjectId,
    preserving the original values if deserialization fails.
    """

    for key, value in obj.items():
        try:
            obj[key] = datetime.fromisoformat(value)  # Try to convert to datetime
        except (ValueError, TypeError):
            try:
                obj[key] = ObjectId(value)
            except errors.InvalidId:
                continue
            continue  # If it fails, keep the original value
    return obj


# Handle all backend events
def handle_events(message):
    """
    Processes backend events based on recieved message.

    :param message: A redis broadcast message
    """

    data = json.loads(message["data"], object_hook=json_deserialize)
    if data["event"] == "user_enrolled":
        # Process the event and update MongoDB
        user = data
        del user["event"]
        mongo.db.users.insert_one(user)
        print("user enrolled on backend.")
    elif data["event"] == "book_borrowed":
        # Process the event and update MongoDB
        borrow_record = data
        del borrow_record["event"]
        mongo.db.borrow_records.insert_one(borrow_record)
        mongo.db.books.update_one(
            {"_id": borrow_record["book_id"]},
            {
                "$set": {
                    "available": False,
                    "available_on": borrow_record["borrowed_until"],
                }
            },
        )
        print("Borrow record registered on backend.")


def stringify_validation_errors(errors_object):
    """
    Create a string representation of a validation error dictionary.

    :param errors_object: Dictionary containing validation errors
    :return: A string with all validation errors
    """
    return reduce(
        lambda accumulator, error: f"{accumulator}\n{error}", errors_object.values(), ""
    )


def is_valid_string(val):
    return checkers.is_string(val) and val.strip()


def is_valid_email(val):
    return checkers.is_email(val)


def is_valid_object_id(val):
    return ObjectId.is_valid(val)


def is_valid_number(val):
    return checkers.is_numeric(val, 1)
