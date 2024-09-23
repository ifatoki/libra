import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from bson.objectid import ObjectId
from app.services import *

class BaseServiceTest(unittest.TestCase):

    def setUp(self):
        # Create mock instances of MongoDB and Redis
        self.mongo = MagicMock()
        self.redis = MagicMock()


class TestEnrollUserService(BaseServiceTest):

    @patch('app.services.datetime')
    def test_enroll_user(self, mock_datetime):
        # Set up mock datetime
        mock_now = datetime(2024, 9, 20)
        mock_datetime.utcnow.return_value = mock_now

        # User data for enrollment
        user_data = {
            'email': 'user@example.com',
            'first_name': 'John',
            'last_name': 'Doe'
        }

        # Call the service function
        result = enroll_user_service(self.mongo, self.redis, user_data)

        # Assert the inserted data
        self.mongo.db.users.insert_one.assert_called_once_with({
            'email': 'user@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'enrollment_date': mock_now
        })

        # Check if Redis publish was called with the correct event
        self.redis.publish.assert_called_once()

        # Verify that the response contains the event
        self.assertEqual(result['email'], 'user@example.com')
        self.assertEqual(result['enrollment_date'], mock_now)


class TestListBooksService(BaseServiceTest):

    def test_list_books(self):
         # Setup default pagination params
        page = 1
        limit = 10
        skip = (page - 1) * limit

        # Mock the books collection
        data = [
            {
                '_id': ObjectId(),
                'title': '1984',
                'author': 'George Orwell',
                'publisher': 'Secker & Warburg',
                'category': 'Dystopian',
                'available': True
            }
        ]
        self.mongo.db.books.find.return_value = data

        # Call the service function
        result = list_books_service(self.mongo)

        # Assert the query was made to fetch available books
        self.mongo.db.books.find.assert_called_once_with({"available": True}, skip=skip, limit=limit)

        # Verify the result
        self.assertEqual(len(result['records']), len(data))
        self.assertEqual(result['records'][0]['title'], '1984')

    def test_list_books_pagination(self):
        # Setup pagination params
        page = 1
        limit = 1

        # Mock the return value of the MongoDB find() query
        self.mongo.db.books.find.return_value = [
            {
                '_id': ObjectId('66eddf68c01bc9ffd69bb433'),
                'title': 'The Sleeping Giant',
                'author': 'Wole Soyinka',
                'publisher': 'Penthouse Publishers',
                'category': 'History',
                'available': True
            }
        ]

        books = list_books_service(self.mongo, page=page, limit=limit)

        self.assertEqual(len(books['records']), limit)
        self.assertEqual(books['records'][0]['title'], 'The Sleeping Giant')

    def test_list_books_service_no_results(self):
        # Setup pagination params
        page = 2
        limit = 2

        # Simulate no books available on this page
        self.mongo.db.books.find.return_value = []

        books = list_books_service(self.mongo, page=page, limit=limit)

        self.assertEqual(len(books['records']), 0)  # No books on this page


class TestGetBookService(BaseServiceTest):

    def test_get_book_success(self):
        # Mock the book document
        book_id = ObjectId()
        self.mongo.db.books.find_one_or_404.return_value = {
            '_id': book_id,
            'title': '1984',
            'author': 'George Orwell',
            'publisher': 'Secker & Warburg',
            'category': 'Dystopian',
            'available': True
        }

        # Call the service function
        result = get_book_service(self.mongo, book_id)

        # Assert the query was made
        self.mongo.db.books.find_one_or_404.assert_called_once_with({"_id": ObjectId(book_id)})

        # Verify the result
        self.assertEqual(result['title'], '1984')
        self.assertEqual(result['available'], True)


class TestFilterBooksService(BaseServiceTest):

    def test_filter_books_by_category_and_author(self):
        # Setup default pagination params
        page = 1
        limit = 10
        skip = (page - 1) * limit

        # Mock the books collection
        data = [
            {
                '_id': ObjectId(),
                'title': '1984',
                'author': 'George Orwell',
                'publisher': 'Secker & Warburg',
                'category': 'Dystopian',
                'available': True
            }
        ]
        self.mongo.db.books.find.return_value = data

        # Call the service function with filters
        result = filter_books_service(self.mongo, category='Dystopian', author='George Orwell')

        # Assert the correct query was made
        self.mongo.db.books.find.assert_called_once_with({
            "available": True,
            "category": "Dystopian",
            "author": "George Orwell"
        }, skip=skip, limit=limit)

        # Verify the result
        self.assertEqual(len(result['records']), len(data))
        self.assertEqual(result['records'][0]['title'], '1984')

    def test_filter_books_service_pagination(self):
        # Setup pagination params
        page = 1
        limit = 1

        # Mock the return value of the MongoDB find() query with filtering
        data = [
            {
                '_id': ObjectId('66eddf68c01bc9ffd69bb433'),
                'title': 'The Sleeping Giant',
                'author': 'Wole Soyinka',
                'publisher': 'Penthouse Publishers',
                'category': 'History',
                'available': True
            }
        ]
        self.mongo.db.books.find.return_value = data

        books = filter_books_service(self.mongo, author='Wole Soyinka', page=page, limit=page)

        self.assertEqual(len(books['records']), len(data))
        self.assertEqual(books['records'][0]['author'], 'Wole Soyinka')

    def test_filter_books_service_no_results(self):
        # Setup pagination params
        page = 1
        limit = 2

        # Simulate no results for the filter and pagination
        data = []
        self.mongo.db.books.find.return_value = data
        books = filter_books_service(self.mongo, author='Nonexistent Author', page=page, limit=limit)

        self.assertEqual(len(books['records']), len(data))  # No books match the filter


class TestBorrowBookService(BaseServiceTest):

    @patch('app.services.datetime')
    @patch('app.services.is_user_existing')
    @patch('app.services.is_book_existing')
    def test_borrow_book_success(self, mock_is_book_existing, mock_is_user_existing, mock_datetime):
        # Mock the datetime
        mock_now = datetime(2024, 9, 20)
        mock_borrow_until = mock_now + timedelta(days=7)
        mock_datetime.utcnow.return_value = mock_now

        # Mock the user and book existence check
        mock_is_user_existing.return_value = True
        mock_is_book_existing.return_value = True

        # Mock the book document
        book_id = ObjectId()
        user_id = ObjectId()
        self.mongo.db.books.find_one.return_value = {'available': True}

        # Call the service function
        result, error, code = borrow_book_service(self.mongo, self.redis, book_id, user_id, 7)

        # Assert that the book is updated as unavailable
        self.mongo.db.books.update_one.assert_called_once_with(
            {"_id": ObjectId(book_id)},
            {"$set": {"available": False}}
        )

        # Assert that a borrow record is inserted
        self.mongo.db.borrow_records.insert_one.assert_called_once()

        # Assert the Redis event is published
        self.redis.publish.assert_called_once()

        # Verify the result
        self.assertEqual(code, 200)
        self.assertIsNone(error)
        self.assertEqual(result['borrowed_until'], mock_borrow_until)


class TestIsUserExisting(BaseServiceTest):

    def test_is_user_existing_by_email(self):
        # Mock the user document
        self.mongo.db.users.find_one.return_value = {'email': 'user@example.com'}

        # Call the service function
        result = is_user_existing(self.mongo, email='user@example.com')

        # Assert the query was made to find the user by email
        self.mongo.db.users.find_one.assert_called_once_with({"email": 'user@example.com'})

        # Verify the result
        self.assertTrue(result)

    def test_is_user_existing_by_id(self):
        # Mock the user document
        user_id = ObjectId()
        self.mongo.db.users.find_one.return_value = {'_id': user_id}

        # Call the service function
        result = is_user_existing(self.mongo, _id=user_id)

        # Assert the query was made to find the user by _id
        self.mongo.db.users.find_one.assert_called_once_with({"_id": ObjectId(user_id)})

        # Verify the result
        self.assertTrue(result)


class TestIsBookExisting(BaseServiceTest):

    def test_is_book_existing(self):
        # Mock the book document
        book_id = ObjectId()
        self.mongo.db.books.find_one.return_value = {'_id': book_id}

        # Call the service function
        result = is_book_existing(self.mongo, book_id)

        # Assert the query was made to find the book by _id
        self.mongo.db.books.find_one.assert_called_once_with({"_id": ObjectId(book_id)})

        # Verify the result
        self.assertTrue(result)
