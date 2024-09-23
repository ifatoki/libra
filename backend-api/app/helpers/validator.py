from app.helpers.utils import (
    is_valid_string,
)


class APIValidator:
    """
    A class to validate data for backend API routes.
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
    def resolve_errors(errors):
        """Resolve the errors and determine if the data is valid."""
        is_valid = len(errors) == 0
        return errors, is_valid
