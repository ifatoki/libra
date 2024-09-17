import json
from app import app, mongo, r
from app.helpers.utils import json_serialize
from flask import request, jsonify
from datetime import datetime
from bson.objectid import ObjectId

# Route to add a new book
@app.route('/admin/books', methods=['POST'])
def add_book():
    data = request.get_json()
    book = {
        "title": data['title'],
        "author": data['author'],
        "publisher": data['publisher'],
        "category": data['category']
    }
    mongo.db.books.insert_one(book)

    book["event"] = "book_added"
    r.publish("frontend_events", json.dumps(book, default=json_serialize))
    return jsonify({"message": "Book added successfully!"}), 201

# Route to remove a book
@app.route('/admin/books/<book_id>', methods=['DELETE'])
def remove_book(book_id):
    result = mongo.db.books.delete_one({"_id": ObjectId(book_id)})
    if result.deleted_count == 0:
        return jsonify({"message": "Book not found"}), 404
    
    book_event = {
        "event": "book_deleted",
        "id": book_id
    }
    r.publish("frontend_events", json.dumps(book_event, default=json_serialize))
    return jsonify({"message": "Book removed successfully!"}), 200

# Route to list all users
@app.route('/admin/users', methods=['GET'])
def list_users():
    users = mongo.db.users.find()
    users_data = [
        {
            'id': str(user['_id']),
            'email': user['email'],
            'first_name': user['first_name'],
            'last_name': user['last_name'],
            'enrollment_date': user['enrollment_date']
        } for user in users
    ]
    return jsonify(users_data), 200

# Route to list all borrow records
@app.route('/admin/borrow-records', methods=['GET'])
def list_borrow_records():
    borrow_records = mongo.db.borrow_records.find()
    borrow_records_data = [
        {
            'id': str(record['_id']),
            'user_id': str(record['user_id']),
            'book_id': str(record['book_id']),
            'borrowed_on': record['borrowed_on'],
            'borrowed_until': record['borrowed_until']
        } for record in borrow_records
    ]
    return jsonify(borrow_records_data), 200

# Route to list books that are not available for borrowing
@app.route('/admin/books/unavailable', methods=['GET'])
def list_unavailable_books():
    now = datetime.utcnow()
    borrow_records = mongo.db.borrow_records.find({"borrowed_until": {"$gte": now}})
    unavailable_books = set(record['book_id'] for record in borrow_records)
    books = mongo.db.books.find({"_id": {"$in": list(unavailable_books)}})
    books_data = [
        {
            'id': str(book['_id']),
            'title': book['title'],
            'author': book['author'],
            'publisher': book['publisher'],
            'category': book['category'],
            'available_until': max(record['borrowed_until'] for record in borrow_records if record['book_id'] == book['_id'])
        } for book in books
    ]
    return jsonify(books_data), 200
