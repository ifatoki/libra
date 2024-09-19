users_borrowed = [
    {
        "$match": {"returned_on": {"$exists": False}}  # Only records where books have not been returned
    },
    {
        "$lookup": {
            "from": "users",  # Join with the users collection
            "localField": "user_id",  # Field from borrow_records
            "foreignField": "_id",  # Field from users
            "as": "user_info"  # Output field
        }
    },
    {
        "$unwind": "$user_info"  # Unwind user_info to get individual user documents
    },
    {
        "$lookup": {
            "from": "books",  # Join with the books collection
            "localField": "book_id",  # Field from borrow_records
            "foreignField": "_id",  # Field from books
            "as": "book_info"  # Output field
        }
    },
    {
        "$unwind": "$book_info"  # Unwind book_info to get individual book documents
    },
    {
        "$group": {
            "_id": {"$toString": "$user_info._id"},  # Convert user_id to string
            "email": {"$first": "$user_info.email"},
            "first_name": {"$first": "$user_info.first_name"},
            "last_name": {"$first": "$user_info.last_name"},
            "enrollment_date": {"$first": "$user_info.enrollment_date"},
            "borrowed_books": {
                "$push": {
                    "_id": {"$toString": "$book_info._id"},  # Convert book_id to string
                    "title": "$book_info.title",
                    "author": "$book_info.author",
                    "publisher": "$book_info.publisher",
                    "category": "$book_info.category"
                }
            }
        }
    }
]