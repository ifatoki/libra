from app.helpers.utils import (
    is_valid_email,
    is_valid_number,
    is_valid_object_id,
    is_valid_string,
)


class APIValidator:
    """
    A class to validate data for frontend API routes like adding books, users,
    filtering, and general API input validation.
    """

    @staticmethod
    def validate_add_book(book_data):
        """Validate data for adding a new book."""

        errors = {}

        if "title" not in book_data or not is_valid_string(book_data["title"]):
            errors["title"] = "Title is required."
        if "author" not in book_data or not is_valid_string(book_data["author"]):
            errors["author"] = "Author is required."
        if "publisher" not in book_data or not is_valid_string(book_data["publisher"]):
            errors["publisher"] = "Publisher is required."
        if "category" not in book_data or not is_valid_string(book_data["category"]):
            errors["category"] = "Category is required."

        return APIValidator.resolve_errors(errors)

    @staticmethod
    def validate_user_enrollment(user_data):
        """Validate user data during enrollment."""
        errors = {}

        if "email" not in user_data or not is_valid_string(user_data["email"]):
            errors["email"] = "Email is required."
        elif not is_valid_email(user_data["email"]):
            errors["email"] = "Invalid email."
        if "first_name" not in user_data or not is_valid_string(
            user_data["first_name"]
        ):
            errors["first_name"] = "First name is required."
        if "last_name" not in user_data or not is_valid_string(user_data["last_name"]):
            errors["last_name"] = "Last name is required."

        return APIValidator.resolve_errors(errors)

    @staticmethod
    def validate_book_borrow(data):
        """Validate parameters for book borrowing"""
        errors = {}

        if "user_id" not in data or not is_valid_object_id(data["user_id"]):
            errors["user_id"] = "valid user_id is required."
        if "days" not in data or not is_valid_number(data["days"]):
            errors["days"] = "Days must be a number greater than 0."

        return APIValidator.resolve_errors(errors)

    @staticmethod
    def resolve_errors(errors):
        """Resolve the errors and determine if the data is valid."""
        is_valid = len(errors) == 0
        return errors, is_valid
