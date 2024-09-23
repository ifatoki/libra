import json
from bson.objectid import ObjectId
from app.helpers.utils import json_serialize
from app.helpers.aggregate_pipelines import users_borrowed


# Dependency injection of services (mongo, redis)
def add_book_service(mongo, redis, book_data):
    book = {
        "title": book_data["title"],
        "author": book_data["author"],
        "publisher": book_data["publisher"],
        "category": book_data["category"],
    }
    mongo.db.books.insert_one(book)

    book_event = book.copy()
    book_event["event"] = "book_added"
    if "_id" in book:
        book["_id"] = str(book["_id"])
    redis.publish("frontend_events", json.dumps(book_event, default=json_serialize))
    return book


def remove_book_service(mongo, redis, book_id):
    result = mongo.db.books.delete_one({"_id": ObjectId(book_id)})
    if result.deleted_count == 0:
        return None

    book_event = {"event": "book_removed", "_id": book_id}
    redis.publish("frontend_events", json.dumps(book_event, default=json_serialize))
    return book_event


def list_users_service(mongo, page=1, limit=10):
    query = {}
    # Calculate how many documents to skip
    skip = (page - 1) * limit

    # Get the total number of users matching the query (before applying skip/limit)
    count = mongo.db.users.count_documents(query)

    # Retrieve paginated results from the database
    users = mongo.db.users.find(query, skip=skip, limit=limit)
    return {
        "page_number": page,
        "page_size": limit,
        "total_record_count": count,
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


def list_users_with_borrowed_books_service(mongo, page=1, limit=10):
    # Calculate how many documents to skip
    skip = (page - 1) * limit

    pipeline = users_borrowed.copy()
    pipeline.append(
        {
            "$facet": {
                "total_count": [{"$count": "count"}],  # Get total count
                "data": [  # Paginated data
                    {"$skip": skip},  # Skip for pagination
                    {"$limit": limit},  # Limit for pagination
                ],
            }
        }
    )

    # Execute the aggregation pipeline
    result = mongo.db.borrow_records.aggregate(pipeline)
    total_count = result["total_count"][0]["count"] if result["total_count"] else 0
    data = result["data"]
    return {
        "page_number": page,
        "page_size": limit,
        "total_record_count": total_count,
        "records": data,
    }


def list_unavailable_books_service(mongo, page=1, limit=10):
    query = {"available": False}

    # Calculate how many documents to skip
    skip = (page - 1) * limit

    # Get the total number of books matching the query (before applying skip/limit)
    total_count = mongo.db.books.count_documents(query)

    # Retrieve paginated results from the database
    unavailable_books = mongo.db.books.find(query, skip=skip, limit=limit)
    return {
        "page_number": page,
        "page_size": limit,
        "total_record_count": total_count,
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
