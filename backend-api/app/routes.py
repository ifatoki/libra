from app import mongo, r
from flask import Blueprint, request, jsonify
from app.services import *

admin_bp = Blueprint('admin_bp', __name__, url_prefix='/admin')

@admin_bp.route('/books', methods=['POST'])
def add_book():
    data = request.get_json()
    book = add_book_service(mongo, r, data)  # Inject dependencies
    return jsonify({"message": "Book added successfully!", "book": book}), 201

@admin_bp.route('/books/<book_id>', methods=['DELETE'])
def remove_book(book_id):
    event = remove_book_service(mongo, r, book_id)
    if event is None:
        return jsonify({"message": "Book not found"}), 404
    return jsonify({"message": "Book removed successfully!"}), 200

@admin_bp.route('/users', methods=['GET'])
def list_users():
    page = int(request.args.get('page', 1))  # Default to page 1 if not provided
    limit = int(request.args.get('limit', 10))  # Default to 10 items per page if not provided

    users_data = list_users_service(mongo, page=page, limit=limit)
    return jsonify(users_data), 200

@admin_bp.route('/users/borrowed', methods=['GET'])
def list_borrow_records():
    records_data = list_users_with_borrowed_books(mongo)
    return jsonify(records_data), 200

@admin_bp.route('/books/unavailable', methods=['GET'])
def list_unavailable_books():
    books_data = list_unavailable_books_service(mongo)
    return jsonify(books_data), 200
