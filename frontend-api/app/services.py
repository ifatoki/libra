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
    user["event"] = "user_enrolled"
    user["_id"] = str(user["_id"])
    redis.publish("backend_events", json.dumps(user, default=json_serialize))

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
def filter_books_service(mongo, publisher=None, category=None):
    query = {"available": True}
    if publisher:
        query["publisher"] = publisher
    if category:
        query["category"] = category

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
    book = mongo.db.books.find_one_or_404({"_id": ObjectId(book_id)})

    if not book['available']:
        return None, "Book is not available for borrowing"

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

    return borrow_record, None
