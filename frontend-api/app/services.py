import json
from flask import Blueprint
from bson.objectid import ObjectId
from datetime import datetime, timedelta
from app.helpers.utils import json_serialize

user_bp = Blueprint('user_bp', __name__)

# Service function to enroll a user
def enroll_user_service(mongo, redis, user_data):
    user = {
        "email": user_data['email'],
        "first_name": user_data['first_name'],
        "last_name": user_data['last_name'],
        "enrollment_date": datetime.utcnow()
    }
    # Insert user into MongoDB
    mongo.db.users.insert_one(user)

    # Publish user enrollment event
    user_event = user.copy()
    user_event["event"] = "user_enrolled"
    if '_id' in user:
        user_event["_id"] = str(user_event["_id"])
    redis.publish("backend_events", json.dumps(user_event, default=json_serialize))

    return user

# Service function to list all available books
def list_books_service(mongo):
    books = mongo.db.books.find({"available": True})
    return [
        {
            'id': str(book['_id']),
            'title': book['title'],
            'author': book['author'],
            'publisher': book['publisher'],
            'category': book['category']
        } for book in books
    ]

# Service function to get a book by its ID
def get_book_service(mongo, book_id):
    book = mongo.db.books.find_one_or_404({"_id": ObjectId(book_id)})
    return {
        'id': str(book['_id']),
        'title': book['title'],
        'author': book['author'],
        'publisher': book['publisher'],
        'category': book['category'],
        'available': book['available']
    }

# Service function to filter books by publisher and/or category
def filter_books_service(mongo, publisher=None, category=None, author=None):
    query = {"available": True}
    if publisher:
        query["publisher"] = publisher
    if category:
        query["category"] = category
    if author:
        query["author"] = author

    books = mongo.db.books.find(query)
    return [
        {
            'id': str(book['_id']),
            'title': book['title'],
            'author': book['author'],
            'publisher': book['publisher'],
            'category': book['category']
        } for book in books
    ]

# Service function to borrow a book
def borrow_book_service(mongo, redis, book_id, user_id, days):
    if not is_user_existing(mongo, user_id):
        return None, "User not found", 404
    if not is_book_existing(mongo, book_id):
        return None, "Book not found", 404

    book = mongo.db.books.find_one({"_id": ObjectId(book_id)})

    if not book['available']:
        return None, "Book is not available for borrowing", 400

    # Mark the book as unavailable
    mongo.db.books.update_one(
        {"_id": ObjectId(book_id)},
        {"$set": {"available": False}}
    )

    # Create a borrow record
    borrowed_until = datetime.utcnow() + timedelta(days=days)
    borrow_record = {
        "user_id": ObjectId(user_id),
        "book_id": ObjectId(book_id),
        "borrowed_on": datetime.utcnow(),
        "borrowed_until": borrowed_until
    }
    mongo.db.borrow_records.insert_one(borrow_record)

    # Publish the borrow event
    borrow_record["event"] = "book_borrowed"
    redis.publish("backend_events", json.dumps(borrow_record, default=json_serialize))

    return borrow_record, None, 200

def is_user_existing(mongo, email = None, id = None):
    """
    Checks if a user with the given email exists in the database.
    
    :param mongo: MongoDB instance
    :param identifier: User's email address or _id
    :return: Boolean value, True if user exists, False otherwise
    """
    existing_user = None
    if email != None:
        existing_user = mongo.db.users.find_one({"email": email})
    elif id != None:
        existing_user = mongo.db.users.find_one({"_id": ObjectId(id)})

    return existing_user is not None

def is_book_existing(mongo, id):
    """
    Checks if a book with the given id exists in the database.
    
    :param mongo: MongoDB instance
    :param id: Book's _id
    :return: Boolean value, True if user exists, False otherwise
    """
    book = mongo.db.books.find_one({"_id": ObjectId(id)})
    return book is not None
