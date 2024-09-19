import unittest
from unittest.mock import patch
from datetime import datetime
from bson import ObjectId
from app.helpers.utils import json_serialize, json_deserialize, handle_events
import json

class TestUtils(unittest.TestCase):

    def setUp(self):
        # Setup initial data
        self.datetime_obj = datetime(2024, 9, 19, 12, 0, 0)
        self.object_id = ObjectId('6509189b3f1a5b5e5c7b10e0')
        self.serialized_data = {
            'date': self.datetime_obj.isoformat(),
            '_id': str(self.object_id)
        }
    
    def test_json_serialize_datetime(self):
        result = json_serialize(self.datetime_obj)
        self.assertEqual(result, self.datetime_obj.isoformat())

    def test_json_serialize_objectid(self):
        result = json_serialize(self.object_id)
        self.assertEqual(result, str(self.object_id))

    def test_json_serialize_invalid(self):
        with self.assertRaises(TypeError):
            json_serialize([])  # Should raise a TypeError for non-serializable types


    def test_json_deserialize_valid(self):
        data = {'date': self.datetime_obj.isoformat(), '_id': str(self.object_id)}
        result = json_deserialize(data)
        self.assertEqual(result['date'], self.datetime_obj)
        self.assertEqual(result['_id'], self.object_id)

    def test_json_deserialize_invalid(self):
        data = {'random': 'invalid'}
        result = json_deserialize(data)
        self.assertEqual(result['random'], 'invalid')  # Should leave non-datetime, non-ObjectId fields unchanged


    @patch('app.helpers.utils.mongo.db.users')
    def test_handle_user_enrolled_event(self, mock_users):
        message = {
            'data': json.dumps({
                'event': 'user_enrolled',
                'email': 'user@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                '_id': str(self.object_id)
            })
        }
        
        # Call the event handler
        handle_events(message)
        
        # Assert the user was inserted into MongoDB
        # mock_users.insert_one.assert_called_once()
        mock_users.insert_one.assert_called_once_with({
            'email': 'user@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            '_id': self.object_id
        })

    @patch('app.helpers.utils.mongo.db.books')
    @patch('app.helpers.utils.mongo.db.borrow_records')
    def test_handle_book_borrowed_event(self, mock_borrow_records, mock_books):
        message = {
            'data': json.dumps({
                'event': 'book_borrowed',
                'book_id': str(self.object_id),
                'borrowed_until': self.datetime_obj.isoformat(),
                '_id': str(self.object_id)
            })
        }
        
        # Call the event handler
        handle_events(message)
        
        # Assert the borrow record was inserted into MongoDB
        # mock_borrow_records.insert_one.assert_called_once()
        mock_borrow_records.insert_one.assert_called_once_with({
            'book_id': self.object_id,
            'borrowed_until': self.datetime_obj,
            '_id': self.object_id
        })
        
        # Assert the book's availability was updated in MongoDB
        mock_books.update_one.assert_called_once_with(
            {"_id": self.object_id},
            {"$set": {"available": False, "available_on": self.datetime_obj}}
        )

if __name__ == '__main__':
    unittest.main()