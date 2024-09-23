from datetime import datetime
import unittest
from unittest.mock import patch
from flask import Flask
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

    @patch('app.routes.list_users_service')
    @patch('app.routes.mongo')
    def test_list_users_route_paginated(self, mongo_mock, list_users_service_mock):
        # Setup default pagination params
        page = 1
        limit = 10

        # Mock the return of the service
        mock_users = [
            {"_id": "user1", "email": "user1@example.com", "first_name": "John", "last_name": "Doe", "enrollment_date": str(datetime.now())},
            {"_id": "user2", "email": "user2@example.com", "first_name": "Jane", "last_name": "Doe", "enrollment_date": str(datetime.now())}
        ]
        service_result = {
            'page_number': page,
            'page_size': limit,
            'total_record_count': len(mock_users),
            'records': mock_users
        }

        # Mock the service to return paginated users
        list_users_service_mock.return_value = service_result

        # Call the endpoint with skip and limit query params
        response = self.client.get(f'/admin/users?page={page}&limit={limit}')

        # Verify the response
        assert response.status_code == 200
        response_data = response.get_json()
        assert len(response_data['records']) == 2
        assert response_data['records'][0]['email'] == "user1@example.com"
        assert response_data['records'][1]['email'] == "user2@example.com"

        # Ensure the service was called with correct skip and limit
        list_users_service_mock.assert_called_with(mongo_mock, page=page, limit=limit)


class TestListBorrowRecordsRoute(BaseTestCase):

    @patch('app.routes.list_users_with_borrowed_books_service')
    @patch('app.routes.mongo')
    def test_list_borrow_records(self, mock_mongo, mock_service):
        # Setup default pagination params
        page = 1
        limit = 10

        # Mock service data
        data = [
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
        service_result = {
            'page_number': page,
            'page_size': limit,
            'total_record_count': len(data),
            'records': data
        }
        mock_service.return_value = service_result

        # Make a GET request to /admin/users/borrowed
        response = self.client.get('/admin/users/borrowed')

        # Assert the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json['records']), 1)
        self.assertEqual(response.json['records'][0]['email'], 'user@example.com')
        self.assertEqual(response.json['total_record_count'], len(data))

        # Ensure the service was called with correct skip and limit
        mock_service.assert_called_with(mock_mongo, page=page, limit=limit)

class TestListUnavailableBooksRoute(BaseTestCase):

    @patch('app.routes.list_unavailable_books_service')
    @patch('app.routes.mongo')
    def test_list_unavailable_books(self, mock_mongo, mock_service):
        # Setup default pagination params
        page = 1
        limit = 10

        # Mock service data
        data = [
            {
                '_id': str(ObjectId()),
                'title': 'The Great Gatsby',
                'author': 'F. Scott Fitzgerald',
                'category': 'fiction',
                'publisher': 'Some Guy',
                'available_on': '2024-09-29T09:37:04.907Z',
                'available': False
            }
        ]
        service_result = {
            'page_number': page,
            'page_size': limit,
            'total_record_count': len(data),
            'records': data
        }
        mock_service.return_value = service_result

        # Make a GET request to /admin/books/unavailable
        response = self.client.get('/admin/books/unavailable')

        # Assert the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json['records']), 1)
        self.assertEqual(response.json['records'][0]['title'], 'The Great Gatsby')

        # Check if service was called correctly
        # mock_mongo.assert_called_once_with(query, page=page, limit=limit)
        mock_service.assert_called_once_with(mock_mongo, page=page, limit=limit)
