import json
from bson.objectid import ObjectId
from datetime import datetime
from app.helpers.utils import json_serialize
from app.helpers.aggregate_pipelines import users_borrowed

# Dependency injection of services (mongo, redis)
def add_book_service(mongo, redis, book_data):
    book = {
        "title": book_data['title'],
        "author": book_data['author'],
        "publisher": book_data['publisher'],
        "category": book_data['category']
    }
    mongo.db.books.insert_one(book)
    
    book_event = book.copy()
    book_event["event"] = "book_added"
    if '_id' in book:
        book['_id'] = str(book['_id'])
    redis.publish("frontend_events", json.dumps(book_event, default=json_serialize))
    return book

def remove_book_service(mongo, redis, book_id):
    result = mongo.db.books.delete_one({"_id": ObjectId(book_id)})
    if result.deleted_count == 0:
        return None
    
    book_event = {
        "event": "book_deleted",
        "_id": book_id
    }
    redis.publish("frontend_events", json.dumps(book_event, default=json_serialize))
    return book_event

def list_users_service(mongo):
    users = mongo.db.users.find()
    return [
        {
            'id': str(user['_id']),
            'email': user['email'],
            'first_name': user['first_name'],
            'last_name': user['last_name'],
            'enrollment_date': user['enrollment_date']
        } for user in users
    ]

def list_users_with_borrowed_books(mongo):
    
    # Execute the aggregation pipeline
    result = list(mongo.db.borrow_records.aggregate(users_borrowed))
    return result

def list_unavailable_books_service(mongo):
    unavailable_books = mongo.db.books.find({ 'available': False })
    return [
        {
            'id': str(book['_id']),
            'title': book['title'],
            'author': book['author'],
            'publisher': book['publisher'],
            'category': book['category'],
            'available_on': str(book['available_on'])
        } for book in unavailable_books
    ]
