import unittest
import json
from unittest.mock import patch, MagicMock
from app.services import (
    add_book_service, 
    remove_book_service, 
    list_users_service, 
    list_users_with_borrowed_books, 
    list_unavailable_books_service
)
from bson.objectid import ObjectId
from datetime import datetime


class TestAddBookService(unittest.TestCase):
    
    @patch('app.mongo')
    @patch('app.redis')
    def test_add_book_service(self, mock_redis, mock_mongo):
        book_data = {
            'title': 'The Great Gatsby',
            'author': 'F. Scott Fitzgerald',
            'publisher': 'Scribner',
            'category': 'Fiction'
        }

        # Simulate MongoDB insertion
        mock_mongo.db.books.insert_one.return_value.inserted_id = ObjectId()

        # Call the service
        result = add_book_service(mock_mongo, mock_redis, book_data)

        # Ensure book was inserted
        mock_mongo.db.books.insert_one.assert_called_once_with(book_data)

        # Ensure Redis publish event was called
        book_data["event"] = "book_added"
        mock_redis.publish.assert_called_once_with(
            "frontend_events", 
            json.dumps(book_data)
        )

        self.assertEqual(result['title'], 'The Great Gatsby')


class TestRemoveBookService(unittest.TestCase):
    
    @patch('app.redis')
    @patch('app.mongo')
    def test_remove_book_service(self, mock_mongo, mock_redis):
        book_id = str(ObjectId())
        
        # Simulate MongoDB deletion
        mock_mongo.db.books.delete_one.return_value.deleted_count = 1

        # Call the service
        result = remove_book_service(mock_mongo, mock_redis, book_id)

        # Ensure the book was removed
        mock_mongo.db.books.delete_one.assert_called_once_with({"_id": ObjectId(book_id)})

        # Ensure Redis event was published
        mock_redis.publish.assert_called_once_with(
            "frontend_events", 
            json.dumps({
                "event": "book_deleted",
                "_id": book_id
            })
        )
        
        self.assertEqual(result['_id'], book_id)

    @patch('app.redis')
    @patch('app.mongo')
    def test_remove_book_service_no_deletion(self, mock_redis, mock_mongo):
        book_id = str(ObjectId())

        # Simulate no book being deleted
        mock_mongo.db.books.delete_one.return_value.deleted_count = 0

        # Call the service
        result = remove_book_service(mock_mongo, mock_redis, book_id)

        # Ensure no event is published and result is None
        mock_redis.publish.assert_not_called()
        self.assertIsNone(result)


class TestListUsersService(unittest.TestCase):

    @patch('app.mongo')
    def test_list_users_service(self, mock_mongo):
        mock_mongo.db.users.find.return_value = [
            {
                '_id': ObjectId(),
                'email': 'user@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'enrollment_date': datetime.utcnow()
            }
        ]

        # Call the service
        result = list_users_service(mock_mongo)

        # Ensure the users were fetched
        mock_mongo.db.users.find.assert_called_once()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['email'], 'user@example.com')


class TestListUsersWithBorrowedBooksService(unittest.TestCase):

    @patch('app.mongo')
    def test_list_users_with_borrowed_books(self, mock_mongo):
        mock_mongo.db.borrow_records.aggregate.return_value = [
            {
                '_id': ObjectId(),
                'email': 'user@example.com',
                'borrowed_books': [
                    {
                        '_id': ObjectId(),
                        'title': 'The Great Gatsby',
                        'author': 'F. Scott Fitzgerald'
                    }
                ]
            }
        ]

        # Call the service
        result = list_users_with_borrowed_books(mock_mongo)

        # Ensure aggregation pipeline was executed
        mock_mongo.db.borrow_records.aggregate.assert_called_once()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['email'], 'user@example.com')


class TestListUnavailableBooksService(unittest.TestCase):

    @patch('app.mongo')
    def test_list_unavailable_books_service(self, mock_mongo):
        mock_mongo.db.books.find.return_value = [
            {
                '_id': ObjectId(),
                'title': 'The Great Gatsby',
                'author': 'F. Scott Fitzgerald',
                'publisher': 'Scribner',
                'category': 'Fiction',
                'available_on': datetime.utcnow()
            }
        ]

        # Call the service
        result = list_unavailable_books_service(mock_mongo)

        # Ensure unavailable books were fetched
        mock_mongo.db.books.find.assert_called_once_with({'available': {'$ne': True}})

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['title'], 'The Great Gatsby')

if __name__ == '__main__':
    unittest.main()