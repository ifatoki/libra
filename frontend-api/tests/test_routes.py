import unittest
from unittest.mock import patch
from flask import Flask, json
from app.routes import *
from bson.objectid import ObjectId

class BaseTestCase(unittest.TestCase):

    def setUp(self):
        # Create a Flask app for testing
        self.app = Flask(__name__)
        self.app.register_blueprint(user_bp)

        # Create a test client
        self.client = self.app.test_client()
        self.app.testing = True

class TestEnrollUserRoute(BaseTestCase):

    @patch('app.routes.is_user_existing')
    @patch('app.routes.enroll_user_service')
    @patch('app.routes.mongo')
    @patch('app.routes.r')
    def test_enroll_user_success(self, mock_redis, mock_mongo, mock_enroll_user_service, mock_is_user_existing):
        # Mock the is_user_existing service
        mock_is_user_existing.return_value = False

        # Mock the enroll_user_service service
        mock_enroll_user_service.return_value = {
            'email': 'user@example.com',
            'first_name': 'John',
            'last_name': 'Doe'
        }

        # Create user data for the request
        user_data = {
            'email': 'user@example.com',
            'first_name': 'John',
            'last_name': 'Doe'
        }

        # Make a POST request to /users
        response = self.client.post('/users', json=user_data)

        # Assert the response
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['message'], 'User enrolled successfully!')
        self.assertEqual(response.json['user']['email'], 'user@example.com')

        # Check if the services were called correctly
        mock_is_user_existing.assert_called_once_with(mock_mongo, 'user@example.com')
        mock_enroll_user_service.assert_called_once_with(mock_mongo, mock_redis, user_data)

    @patch('app.routes.is_user_existing')
    @patch('app.routes.mongo')
    def test_enroll_user_existing(self, mock_mongo, mock_is_user_existing):
        # Mock the is_user_existing service
        mock_is_user_existing.return_value = True

        # Create user data for the request
        user_data = {
            'email': 'user@example.com',
            'first_name': 'John',
            'last_name': 'Doe'
        }

        # Make a POST request to /users
        response = self.client.post('/users', json=user_data)

        # Assert the response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['message'], 'User with this email already exists')

        # Check if the service was called correctly
        mock_is_user_existing.assert_called_once_with(mock_mongo, 'user@example.com')

class TestListBooksRoute(BaseTestCase):

    @patch('app.routes.list_books_service')
    @patch('app.routes.mongo')
    def test_list_books(self, mock_mongo, mock_list_books_service):
        # Mock the service data
        mock_list_books_service.return_value = [
            {
                'title': 'The Great Gatsby',
                'author': 'F. Scott Fitzgerald'
            }
        ]

        # Make a GET request to /books
        response = self.client.get('/books')

        # Assert the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 1)
        self.assertEqual(response.json[0]['title'], 'The Great Gatsby')

        # Check if the service was called correctly
        mock_list_books_service.assert_called_once_with(mock_mongo)


class TestGetBookRoute(BaseTestCase):

    @patch('app.routes.is_book_existing')
    @patch('app.routes.get_book_service')
    @patch('app.routes.mongo')
    def test_get_book_success(self, mock_mongo, mock_get_book_service, mock_is_book_existing):
        # Mock the is_book_existing service
        mock_is_book_existing.return_value = True

        # Mock the get_book_service service
        mock_get_book_service.return_value = {
            'title': 'The Great Gatsby',
            'author': 'F. Scott Fitzgerald'
        }

        # Make a GET request to /books/<book_id>
        book_id = str(ObjectId())
        response = self.client.get(f'/books/{book_id}')

        # Assert the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['title'], 'The Great Gatsby')

        # Check if the services were called correctly
        mock_is_book_existing.assert_called_once_with(mock_mongo, book_id)
        mock_get_book_service.assert_called_once_with(mock_mongo, book_id)

    @patch('app.routes.is_book_existing')
    @patch('app.routes.mongo')
    def test_get_book_not_found(self, mock_mongo, mock_is_book_existing):
        # Mock the is_book_existing service
        mock_is_book_existing.return_value = False

        # Make a GET request to /books/<book_id>
        book_id = str(ObjectId())
        response = self.client.get(f'/books/{book_id}')

        # Assert the response
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json['message'], 'Book not found')

        # Check if the service was called correctly
        mock_is_book_existing.assert_called_once_with(mock_mongo, book_id)


class TestFilterBooksRoute(BaseTestCase):

    @patch('app.routes.filter_books_service')
    @patch('app.routes.mongo')
    def test_filter_books(self, mock_mongo, mock_filter_books_service):
        # Mock the service data
        mock_filter_books_service.return_value = [
            {
                'title': 'The Great Gatsby',
                'author': 'F. Scott Fitzgerald'
            }
        ]

        # Make a GET request to /books with query params
        response = self.client.get('/books', query_string={'author': 'F. Scott Fitzgerald'})

        # Assert the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 1)
        self.assertEqual(response.json[0]['author'], 'F. Scott Fitzgerald')

        # Check if the service was called correctly
        mock_filter_books_service.assert_called_once_with(mock_mongo, None, None, 'F. Scott Fitzgerald')

class TestBorrowBookRoute(BaseTestCase):

    @patch('app.routes.borrow_book_service')
    @patch('app.routes.mongo')
    @patch('app.routes.r')
    def test_borrow_book_success(self, mock_redis, mock_mongo, mock_borrow_book_service):
        # Mock the borrow_book_service service
        mock_borrow_book_service.return_value = ({
            'borrowed_until': '2024-09-30'
        }, None, 200)

        # Create borrow data for the request
        borrow_data = {
            'user_id': str(ObjectId()),
            'days': 7
        }

        # Make a POST request to /books/<book_id>/borrow
        book_id = str(ObjectId())
        response = self.client.post(f'/books/{book_id}/borrow', json=borrow_data)

        # Assert the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], 'Book borrowed until 2024-09-30')

        # Check if the service was called correctly
        mock_borrow_book_service.assert_called_once_with(mock_mongo, mock_redis, book_id, borrow_data['user_id'], borrow_data['days'])

    @patch('app.routes.borrow_book_service')
    @patch('app.routes.mongo')
    @patch('app.routes.r')
    def test_borrow_book_failure(self, mock_redis, mock_mongo, mock_borrow_book_service):
        # Mock the borrow_book_service service (borrow fails)
        mock_borrow_book_service.return_value = (None, 'Book not available', 400)

        # Create borrow data for the request
        borrow_data = {
            'user_id': str(ObjectId()),
            'days': 7
        }

        # Make a POST request to /books/<book_id>/borrow
        book_id = str(ObjectId())
        response = self.client.post(f'/books/{book_id}/borrow', json=borrow_data)

        # Assert the response
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['message'], 'Book not available')

        # Check if the service was called correctly
        mock_borrow_book_service.assert_called_once_with(mock_mongo, mock_redis, book_id, borrow_data['user_id'], borrow_data['days'])
