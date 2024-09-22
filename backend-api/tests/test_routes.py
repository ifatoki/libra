from datetime import datetime
import unittest
from unittest.mock import patch, MagicMock
from flask import Flask, json
from app.routes import admin_bp
from bson.objectid import ObjectId


class BaseTestCase(unittest.TestCase):

    def setUp(self):
        # Create a Flask app for testing
        self.app = Flask(__name__)
        self.app.register_blueprint(admin_bp)

        # Create a test client
        self.client = self.app.test_client()
        self.app.testing = True


class TestAddBookRoute(BaseTestCase):

    @patch('app.routes.add_book_service')
    @patch('app.routes.mongo')
    @patch('app.routes.r')
    def test_add_book(self, mock_redis, mock_mongo, mock_add_book_service):
        # Mock the book data and service
        mock_add_book_service.return_value = {
            '_id': str(ObjectId()),
            'title': 'The Great Gatsby',
            'author': 'F. Scott Fitzgerald',
            'publisher': 'Scribner',
            'category': 'Fiction'
        }

        # Create book data for request
        book_data = {
            'title': 'The Great Gatsby',
            'author': 'F. Scott Fitzgerald',
            'publisher': 'Scribner',
            'category': 'Fiction'
        }

        # Make a POST request to /admin/books
        response = self.client.post('/admin/books', json=book_data)

        # Assert the response
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['message'], 'Book added successfully!')
        self.assertEqual(response.json['book']['title'], 'The Great Gatsby')

        # Check if service was called correctly
        mock_add_book_service.assert_called_once_with(mock_mongo, mock_redis, book_data)


class TestRemoveBookRoute(BaseTestCase):

    @patch('app.routes.remove_book_service')
    @patch('app.routes.mongo')
    @patch('app.routes.r')
    def test_remove_book_success(self, mock_redis, mock_mongo, mock_remove_book_service):
        # Simulate successful deletion
        mock_remove_book_service.return_value = {
            'event': 'book_removed',
            '_id': str(ObjectId())
        }

        # Make a DELETE request to /admin/books/<book_id>
        book_id = str(ObjectId())
        response = self.client.delete(f'/admin/books/{book_id}')

        # Assert the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], 'Book removed successfully!')

        # Check if service was called correctly
        mock_remove_book_service.assert_called_once_with(mock_mongo, mock_redis, book_id)

    @patch('app.routes.remove_book_service')
    @patch('app.routes.mongo')
    @patch('app.routes.r')
    def test_remove_book_not_found(self, mock_redis, mock_mongo, mock_remove_book_service):
        # Simulate book not found
        mock_remove_book_service.return_value = None

        # Make a DELETE request to /admin/books/<book_id>
        book_id = str(ObjectId())
        response = self.client.delete(f'/admin/books/{book_id}')

        # Assert the response
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['message'], 'Book not found')

        # Check if service was called correctly
        mock_remove_book_service.assert_called_once_with(mock_mongo, mock_redis, book_id)

class TestListUsersRoute(BaseTestCase):

    @patch('app.routes.list_users_service')
    @patch('app.routes.mongo')
    def test_list_users(self, mock_mongo, mock_list_users_service):
        # Mock service data
        mock_list_users_service.return_value = [
            {
                'id': str(ObjectId()),
                'email': 'user@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'enrollment_date': '2024-09-17T09:37:04.907Z'
            }
        ]

        # Make a GET request to /admin/users
        response = self.client.get('/admin/users')

        # Assert the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 1)
        self.assertEqual(response.json[0]['email'], 'user@example.com')

        # Setup default pagination params
        page = 1
        limit = 10

        # Check if service was called correctly
        mock_list_users_service.assert_called_once_with(mock_mongo, page=page, limit=limit)

    @patch('app.routes.mongo')
    def test_list_users_route_paginated(self, mongo_mock):
        # Mock the return of the service
        mock_users = [
            {"_id": "user1", "email": "user1@example.com", "first_name": "John", "last_name": "Doe", "enrollment_date": str(datetime.now())},
            {"_id": "user2", "email": "user2@example.com", "first_name": "Jane", "last_name": "Doe", "enrollment_date": str(datetime.now())}
        ]

        # Mock the service to return paginated users
        mongo_mock.db.users.find.return_value = mock_users

        # Call the endpoint with skip and limit query params
        response = self.client.get('/admin/users?skip=0&limit=2')

        # Verify the response
        assert response.status_code == 200
        response_data = response.get_json()
        assert len(response_data) == 2
        assert response_data[0]['email'] == "user1@example.com"
        assert response_data[1]['email'] == "user2@example.com"

        # Ensure the service was called with correct skip and limit
        mongo_mock.db.users.find.assert_called_with(skip=0, limit=2)


class TestListBorrowRecordsRoute(BaseTestCase):

    @patch('app.routes.list_users_with_borrowed_books')
    @patch('app.routes.mongo')
    def test_list_borrow_records(self, mock_mongo, mock_list_borrow_records_service):
        # Mock service data
        mock_list_borrow_records_service.return_value = [
            {
                'id': str(ObjectId()),
                'email': 'user@example.com',
                'borrowed_books': [
                    {
                        'title': 'The Great Gatsby',
                        'author': 'F. Scott Fitzgerald'
                    }
                ]
            }
        ]

        # Make a GET request to /admin/users/borrowed
        response = self.client.get('/admin/users/borrowed')

        # Setup default pagination params
        page = 1
        limit = 10

        # Assert the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 1)
        self.assertEqual(response.json[0]['email'], 'user@example.com')

        # Check if service was called correctly
        mock_list_borrow_records_service.assert_called_once_with(mock_mongo, page=page, limit=limit)

class TestListUnavailableBooksRoute(BaseTestCase):

    @patch('app.routes.list_unavailable_books_service')
    @patch('app.routes.mongo')
    def test_list_unavailable_books(self, mock_mongo, mock_list_unavailable_books_service):
        # Mock service data
        mock_list_unavailable_books_service.return_value = [
            {
                'id': str(ObjectId()),
                'title': 'The Great Gatsby',
                'author': 'F. Scott Fitzgerald',
                'available_on': '2024-09-29T09:37:04.907Z'
            }
        ]

        # Make a GET request to /admin/books/unavailable
        response = self.client.get('/admin/books/unavailable')

        # Setup default pagination params
        page = 1
        limit = 10

        # Assert the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 1)
        self.assertEqual(response.json[0]['title'], 'The Great Gatsby')

        # Check if service was called correctly
        mock_list_unavailable_books_service.assert_called_once_with(mock_mongo, page=page, limit=limit)

