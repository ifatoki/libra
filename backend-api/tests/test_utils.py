import unittest
from bson import ObjectId
from datetime import datetime
from unittest.mock import MagicMock, patch
from app.helpers.utils import json_serialize, json_deserialize, handle_events
import json

class TestJsonSerialize(unittest.TestCase):

    def test_serialize_datetime(self):
        # Test serializing a datetime object
        test_datetime = datetime(2024, 9, 20, 14, 30)
        result = json_serialize(test_datetime)
        
        # Assert the datetime is converted to ISO 8601 format
        self.assertEqual(result, "2024-09-20T14:30:00")

    def test_serialize_objectid(self):
        # Test serializing an ObjectId
        test_objectid = ObjectId()
        result = json_serialize(test_objectid)
        
        # Assert the ObjectId is converted to string
        self.assertEqual(result, str(test_objectid))

    def test_serialize_invalid_type(self):
        # Test serializing an unsupported type
        with self.assertRaises(TypeError):
            json_serialize([])  # List is not serializable

class TestJsonDeserialize(unittest.TestCase):

    def test_deserialize_datetime(self):
        # Test deserializing an ISO 8601 datetime string
        obj = {'key': '2024-09-20T14:30:00'}
        result = json_deserialize(obj)
        
        # Assert the datetime string is converted back to datetime object
        self.assertIsInstance(result['key'], datetime)
        self.assertEqual(result['key'], datetime(2024, 9, 20, 14, 30))

    def test_deserialize_objectid(self):
        # Test deserializing an ObjectId string
        obj = {'key': str(ObjectId())}
        result = json_deserialize(obj)
        
        # Assert the ObjectId string is converted back to ObjectId object
        self.assertIsInstance(result['key'], ObjectId)

    def test_deserialize_invalid_type(self):
        # Test that deserialization ignores non-datetime, non-ObjectId values
        obj = {'key': 'some_random_string'}
        result = json_deserialize(obj)
        
        # Assert the value remains unchanged
        self.assertEqual(result['key'], 'some_random_string')

class TestHandleEventsBackend(unittest.TestCase):

    @patch('app.helpers.utils.mongo')
    @patch('app.helpers.utils.json.loads')
    def test_handle_user_enrolled_event(self, mock_json_loads, mock_mongo):
        # Mock the incoming message
        mock_json_loads.return_value = {
            'event': 'user_enrolled',
            '_id': ObjectId(),
            'email': 'user@example.com',
            'first_name': 'John',
            'last_name': 'Doe'
        }

        # Mock message
        message = {'data': '{"event": "user_enrolled"}'}
        
        # Call the function
        handle_events(message)

        # Assert the MongoDB insert_one was called with the correct data
        expected_data = {
            '_id': mock_json_loads.return_value['_id'],
            'email': 'user@example.com',
            'first_name': 'John',
            'last_name': 'Doe'
        }
        mock_mongo.db.users.insert_one.assert_called_once_with(expected_data)

    @patch('app.helpers.utils.mongo')
    @patch('app.helpers.utils.json.loads')
    def test_handle_book_borrowed_event(self, mock_json_loads, mock_mongo):
        # Mock the incoming message
        mock_json_loads.return_value = {
            'event': 'book_borrowed',
            'user_id': ObjectId(),
            'book_id': ObjectId(),
            'borrowed_until': datetime.utcnow()
        }

        # Mock message
        message = {'data': '{"event": "book_borrowed"}'}
        
        # Call the function
        handle_events(message)

        # Assert the MongoDB insert_one for borrow_records was called with the correct data
        expected_borrow_record = {
            'user_id': mock_json_loads.return_value['user_id'],
            'book_id': mock_json_loads.return_value['book_id'],
            'borrowed_until': mock_json_loads.return_value['borrowed_until']
        }
        mock_mongo.db.borrow_records.insert_one.assert_called_once_with(expected_borrow_record)

        # Assert the MongoDB update_one for books was called with the correct query
        mock_mongo.db.books.update_one.assert_called_once_with(
            {"_id": mock_json_loads.return_value['book_id']},
            {"$set": {
                "available": False,
                "available_on": mock_json_loads.return_value['borrowed_until']
            }}
        )
