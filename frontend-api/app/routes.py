from app import app, mongo
from flask import request, jsonify
from datetime import datetime, timedelta
from bson.objectid import ObjectId

# Route to enroll a new user
@app.route('/users', methods=['POST'])
def enroll_user():
    data = request.get_json()
    user = {
        "email": data['email'],
        "first_name": data['first_name'],
        "last_name": data['last_name'],
        "enrollment_date": datetime.utcnow()
    }
    # Insert user into MongoDB
    mongo.db.users.insert_one(user)
    return jsonify({"message": "User enrolled successfully!"}), 201

# Route to list all available books
@app.route('/books', methods=['GET'])
def list_books():
    books = mongo.db.books.find({"available": True})
    books_data = [
        {
            'id': str(book['_id']),
            'title': book['title'],
            'author': book['author'],
            'publisher': book['publisher'],
            'category': book['category']
        } for book in books
    ]
    return jsonify(books_data), 200

# Route to get a single book by its ID
@app.route('/books/<book_id>', methods=['GET'])
def get_book(book_id):
    book = mongo.db.books.find_one_or_404({"_id": ObjectId(book_id)})
    book_data = {
        'id': str(book['_id']),
        'title': book['title'],
        'author': book['author'],
        'publisher': book['publisher'],
        'category': book['category'],
        'available': book['available']
    }
    return jsonify(book_data), 200

# Route to filter books by publisher or category
@app.route('/books/filter', methods=['GET'])
def filter_books():
    publisher = request.args.get('publisher')
    category = request.args.get('category')

    query = {"available": True}

    if publisher:
        query["publisher"] = publisher
    if category:
        query["category"] = category

    books = mongo.db.books.find(query)
    books_data = [
        {
            'id': str(book['_id']),
            'title': book['title'],
            'author': book['author'],
            'publisher': book['publisher'],
            'category': book['category']
        } for book in books
    ]
    return jsonify(books_data), 200

# Route to borrow a book by its ID
@app.route('/books/<book_id>/borrow', methods=['POST'])
def borrow_book(book_id):
    data = request.get_json()
    user_id = data['user_id']
    days = data['days']

    book = mongo.db.books.find_one_or_404({"_id": ObjectId(book_id)})

    # Check if the book is available
    if not book['available']:
        return jsonify({"message": "Book is not available for borrowing"}), 400

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

    return jsonify({"message": f"Book borrowed until {borrowed_until}"}), 200
