from flask import Blueprint, request, jsonify
from app import mongo, r
from app.services import *

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/users', methods=['POST'])
def enroll_user():
    data = request.get_json()
    
    if is_user_existing(mongo, email=data['email']):
        return jsonify({"message": "User with this email already exists"}), 400
    user = enroll_user_service(mongo, r, data)
    return jsonify({"message": "User enrolled successfully!", "user": user}), 201

@user_bp.route('/books/<book_id>/borrow', methods=['POST'])
def borrow_book(book_id):
    data = request.get_json()
    user_id = data['user_id']
    days = data['days']

    borrow_record, error, code = borrow_book_service(mongo, r, book_id, user_id, days)
    if error:
        return jsonify({"message": error}), code

    return jsonify({"message": f"Book borrowed until {borrow_record['borrowed_until']}"}), 200

@user_bp.route('/books/<book_id>', methods=['GET'])
def get_book(book_id):
    if not is_book_existing(mongo, book_id):
        return jsonify({"message": "Book not found"}), 404
    book_data = get_book_service(mongo, book_id)
    return jsonify(book_data), 200

@user_bp.route('/books', methods=['GET'])
def filter_books():
    publisher = request.args.get('publisher')
    category = request.args.get('category')
    author = request.args.get('author')
    books_data = []

    if publisher or category or author:
        books_data = filter_books_service(mongo, publisher, category, author)
    else:
        books_data = list_books_service(mongo)
    return jsonify(books_data), 200
