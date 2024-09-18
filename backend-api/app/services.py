import json
from bson.objectid import ObjectId
from datetime import datetime
from app.helpers.utils import json_serialize

# Dependency injection of services (mongo, redis)
def add_book_service(mongo, redis, book_data):
    book = {
        "title": book_data['title'],
        "author": book_data['author'],
        "publisher": book_data['publisher'],
        "category": book_data['category']
    }
    mongo.db.books.insert_one(book)
    
    book["event"] = "book_added"
    book['_id'] = str(book['_id'])
    redis.publish("frontend_events", json.dumps(book, default=json_serialize))
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

def list_borrow_records_service(mongo):
    borrow_records = mongo.db.borrow_records.find()
    return [
        {
            'id': str(record['_id']),
            'user_id': str(record['user_id']),
            'book_id': str(record['book_id']),
            'borrowed_on': record['borrowed_on'],
            'borrowed_until': record['borrowed_until']
        } for record in borrow_records
    ]

def list_unavailable_books_service(mongo):
    now = datetime.utcnow()
    borrow_records = mongo.db.borrow_records.find({"borrowed_until": {"$gte": now}})
    unavailable_books = set(record['book_id'] for record in borrow_records)
    books = mongo.db.books.find({"_id": {"$in": list(unavailable_books)}})
    
    return [
        {
            'id': str(book['_id']),
            'title': book['title'],
            'author': book['author'],
            'publisher': book['publisher'],
            'category': book['category'],
            'available_until': max(record['borrowed_until'] for record in borrow_records if record['book_id'] == book['_id'])
        } for book in books
    ]
