from flask import Blueprint, request, jsonify
from app import mongo, r
from app.services import (
    enroll_user_service,
    borrow_book_service,
    is_book_existing,
    is_user_existing,
    get_book_service,
    filter_books_service,
    list_books_service,
)
from app.helpers.utils import stringify_validation_errors
from app.helpers.validator import APIValidator

user_bp = Blueprint("user_bp", __name__)


@user_bp.route("/users", methods=["POST"])
def enroll_user():
    data = request.get_json()

    # Validate the user data
    errors, is_valid = APIValidator.validate_user_enrollment(data)

    if not is_valid:
        return jsonify({"message": stringify_validation_errors(errors)}), 400

    if is_user_existing(mongo, email=data["email"]):
        return jsonify({"message": "User with this email already exists"}), 400
    user = enroll_user_service(mongo, r, data)
    return jsonify({"message": "User enrolled successfully!", "user": user}), 201


@user_bp.route("/books/<book_id>/borrow", methods=["POST"])
def borrow_book(book_id):
    data = request.get_json()

    # Validate the book data
    errors, is_valid = APIValidator.validate_book_borrow(data)
    if not is_valid:
        return jsonify({"errors": stringify_validation_errors(errors)}), 400

    user_id = data["user_id"]
    days = data["days"]

    borrow_record, error, code = borrow_book_service(mongo, r, book_id, user_id, days)
    if error:
        return jsonify({"message": error}), code

    return jsonify(
        {"message": f"Book borrowed until {borrow_record['borrowed_until']}"}
    ), 200


@user_bp.route("/books/<book_id>", methods=["GET"])
def get_book(book_id):
    if not is_book_existing(mongo, book_id):
        return jsonify({"message": "Book not found"}), 404
    book_data = get_book_service(mongo, book_id)
    return jsonify(book_data), 200


@user_bp.route("/books", methods=["GET"])
def filter_books():
    publisher = request.args.get("publisher")
    category = request.args.get("category")
    author = request.args.get("author")
    page = int(request.args.get("page", 1))  # Default to page 1 if not provided
    limit = int(
        request.args.get("limit", 10)
    )  # Default to 10 items per page if not provided

    books_data = []

    if publisher or category or author:
        books_data = filter_books_service(
            mongo, publisher, category, author, page, limit
        )
    else:
        books_data = list_books_service(mongo, page, limit)

    return jsonify(books_data), 200
