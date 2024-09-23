import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.services import (
    add_book_service,
    remove_book_service,
    list_users_service,
    list_users_with_borrowed_books_service,
    list_unavailable_books_service,
)
from bson.objectid import ObjectId


class BaseServiceTest(unittest.TestCase):
    def setUp(self):
        # Create mock instances of MongoDB and Redis
        self.mongo = MagicMock()
        self.redis = MagicMock()


class TestAddBookService(BaseServiceTest):
    @patch("app.services.json_serialize")
    @patch("app.services.json.dumps")
    def test_add_book_service(self, mock_json_dumps, mock_json_serialize):
        # Sample book data
        book_data = {
            "title": "Sample Title",
            "author": "Sample Author",
            "publisher": "Sample Publisher",
            "category": "Sample Category",
        }

        # Call the service
        result = add_book_service(self.mongo, self.redis, book_data)

        # Assert book is inserted in MongoDB
        self.mongo.db.books.insert_one.assert_called_once_with(book_data)

        # Prepare the book event data
        book_event = book_data.copy()
        book_event["event"] = "book_added"

        # Assert event is published to Redis
        mock_json_dumps.assert_called_once_with(book_event, default=mock_json_serialize)
        self.redis.publish.assert_called_once_with(
            "frontend_events", mock_json_dumps.return_value
        )

        # Assert return value is the same book data
        self.assertEqual(result, book_data)


class TestRemoveBookService(BaseServiceTest):
    @patch("app.services.json_serialize")
    @patch("app.services.json.dumps")
    def test_remove_book_service_success(self, mock_json_dumps, mock_json_serialize):
        # Mock a successful deletion from MongoDB
        self.mongo.db.books.delete_one.return_value.deleted_count = 1

        # Book ID to be removed
        book_id = str(ObjectId())

        # Call the service
        result = remove_book_service(self.mongo, self.redis, book_id)

        # Assert the book was removed from MongoDB
        self.mongo.db.books.delete_one.assert_called_once_with(
            {"_id": ObjectId(book_id)}
        )

        # Prepare the expected book event
        book_event = {"event": "book_removed", "_id": book_id}

        # Assert event is published to Redis
        mock_json_dumps.assert_called_once_with(book_event, default=mock_json_serialize)
        self.redis.publish.assert_called_once_with(
            "frontend_events", mock_json_dumps.return_value
        )

        # Assert return value is the book event
        self.assertEqual(result, book_event)

    def test_remove_book_service_not_found(self):
        # Mock a failed deletion from MongoDB (book not found)
        self.mongo.db.books.delete_one.return_value.deleted_count = 0

        # Book ID to be removed
        book_id = str(ObjectId())

        # Call the service
        result = remove_book_service(self.mongo, self.redis, book_id)

        # Assert the book was not removed
        self.mongo.db.books.delete_one.assert_called_once_with(
            {"_id": ObjectId(book_id)}
        )

        # Assert Redis publish was not called
        self.redis.publish.assert_not_called()

        # Assert return value is None
        self.assertIsNone(result)


class TestListUsersService(BaseServiceTest):
    def test_list_users_service(self):
        # Mock user data from MongoDB
        users = [
            {
                "_id": ObjectId(),
                "email": "user1@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "enrollment_date": datetime.utcnow(),
            },
            {
                "_id": ObjectId(),
                "email": "user2@example.com",
                "first_name": "Jane",
                "last_name": "Doe",
                "enrollment_date": datetime.utcnow(),
            },
        ]
        self.mongo.db.users.find.return_value = users
        self.mongo.db.users.count_documents.return_value = len(users)

        # Call the service
        result = list_users_service(self.mongo)

        # Assert the expected result
        expected_result = {
            "page_number": 1,
            "page_size": 10,
            "total_record_count": len(users),
            "records": [
                {
                    "_id": str(user["_id"]),
                    "email": user["email"],
                    "first_name": user["first_name"],
                    "last_name": user["last_name"],
                    "enrollment_date": user["enrollment_date"],
                }
                for user in users
            ],
        }

        # Assert the result matches expected output
        self.assertEqual(result, expected_result)

        # Assert MongoDB query was called
        self.mongo.db.users.find.assert_called_once()

    def test_list_users_service_paginated(self):
        # Mocked users returned from the database
        mock_users = [
            {
                "_id": ObjectId(),
                "email": "user1@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "enrollment_date": datetime.now(),
            },
            {
                "_id": ObjectId(),
                "email": "user2@example.com",
                "first_name": "Jane",
                "last_name": "Doe",
                "enrollment_date": datetime.now(),
            },
        ]

        # Setting up the mock for find with pagination
        self.mongo.db.users.find.return_value = mock_users
        self.mongo.db.users.count_documents.return_value = len(mock_users)

        # Call the service with a page and limit
        page = 1
        limit = 2
        skip = skip = (page - 1) * limit
        result = list_users_service(self.mongo, page=page, limit=limit)

        # Check if the result matches the mock data
        assert len(result["records"]) == 2
        assert result["records"][0]["email"] == "user1@example.com"
        assert result["records"][1]["email"] == "user2@example.com"

        # Assert that the right query was made with skip and limit
        self.mongo.db.users.find.assert_called_with({}, skip=skip, limit=limit)


class TestListUsersWithBorrowedBooksService(BaseServiceTest):
    def test_list_users_with_borrowed_books(self):
        # Mock pipeline execution result
        data = [
            {
                "_id": ObjectId(),
                "email": "user@example.com",
                "borrowed_books": [
                    {
                        "_id": ObjectId(),
                        "title": "The Great Gatsby",
                        "author": "F. Scott Fitzgerald",
                    }
                ],
            }
        ]
        expected_result = {"total_count": [{"count": 4}], "data": data}
        self.mongo.db.borrow_records.aggregate.return_value = expected_result

        # Call the service
        result = list_users_with_borrowed_books_service(self.mongo)

        # Ensure aggregation pipeline was executed
        self.mongo.db.borrow_records.aggregate.assert_called_once()

        self.assertEqual(len(result["records"]), len(data))
        self.assertEqual(result["records"][0]["email"], "user@example.com")


class TestListUnavailableBooksService(BaseServiceTest):
    def test_list_unavailable_books_service(self):
        # Set default pagination params
        page = 1
        limit = 10

        # Mock unavailable books from MongoDB
        unavailable_books = [
            {
                "_id": ObjectId(),
                "title": "Book 1",
                "author": "Author 1",
                "publisher": "Publisher 1",
                "category": "Category 1",
                "available_on": datetime.utcnow(),
            },
            {
                "_id": ObjectId(),
                "title": "Book 2",
                "author": "Author 2",
                "publisher": "Publisher 2",
                "category": "Category 2",
                "available_on": datetime.utcnow(),
            },
        ]
        self.mongo.db.books.find.return_value = unavailable_books
        self.mongo.db.books.count_documents.return_value = 12

        # Call the service
        result = list_unavailable_books_service(self.mongo)

        # Prepare the expected result
        expected_result = {
            "page_number": page,
            "page_size": limit,
            "total_record_count": 12,
            "records": [
                {
                    "_id": str(book["_id"]),
                    "title": book["title"],
                    "author": book["author"],
                    "publisher": book["publisher"],
                    "category": book["category"],
                    "available_on": str(book["available_on"]),
                }
                for book in unavailable_books
            ],
        }

        # Call the service with a page and limit
        limit = 10
        skip = 0

        # Assert the result matches the expected output
        self.assertEqual(result, expected_result)

        # Assert MongoDB query was called
        self.mongo.db.books.find.assert_called_once_with(
            {"available": False}, skip=skip, limit=limit
        )
