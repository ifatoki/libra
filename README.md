# Libra

This project is a **Library Management System** that consists of two independent APIs:
- **Frontend API**: For user-facing operations like user enrollment, browsing books, and borrowing.
- **Backend/Admin API**: For administrative operations like adding/removing books, managing users, and handling borrowing information.

The system uses **Flask** for the web framework, **MongoDB** for data storage, **Redis** for handling events, and follows a **microservices** architecture with separate services for frontend and backend logic.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Technologies](#technologies)
- [Setup Instructions](#setup-instructions)
- [API Endpoints](#api-endpoints)
- [Running Unit Tests](#running-unit-tests)
- [Event-Driven Approach](#event-driven-approach)
- [License](#license)

## Features

### User Features (Frontend API)
- **User Enrollment**: Users can register in the library using their email, firstname and lastname.
- **Browse Books**: 
  * Users can list all available books.
  * Users can get a single book by its ID.
  * Users can filter books 
    * by publishers e.g Wiley, Apress, Manning 
    * by category e.g fiction, technology, science
- **Borrow Books**: Users can borrow available books by ID specifying how long they want it.

### Admin Features (Backend API)
- **Add Books**: Admins can add books to the catalogue.
- **Remove Books**: Admins can remove books from the catalogue.
- **List Users**: 
  * Admins can list all registered users 
  * Admins can list all users with borrowed books and the books they have borrowed.
- **List Unavailable Books**: Admins can see books that are currently borrowed.

### Event-Driven Design
- **User Enrollment Event**: Publishes events when a user is enrolled.
- **Book Borrowed Event**: Publishes events when a book is borrowed.
- **Book Added Event**: Publishes events when a book is added.
- **Book Deleted Event**: Publishes events when a book is deleted.

## Architecture

The project is organized into the following components:

- **Frontend API**:
  - Handles user-facing functionalities.
  - Manages user enrollment and book browsing.
  - Interacts with **Redis** to communicate user events to the backend.
  
- **Backend API**:
  - Handles admin functionalities like adding/removing books and managing borrowed books.
  - Publishes events to **Redis** for synchronizing with the frontend system.

- **MongoDB**:
  - Stores data related to users, books, and borrowing records.

- **Redis**:
  - Used for event-driven communication between the two APIs (frontend and backend).

## Technologies

- **Python 3.x**
- **Flask**: Lightweight web framework.
- **MongoDB**: NoSQL database to store user, book, and borrow data.
- **Redis**: Message broker to manage communication between microservices.
- **Pytest**: Testing framework to ensure code quality.
- **Docker**: For containerization of the API.

## Setup Instructions

### Prerequisites

- **Python 3.x**
- **MongoDB** installed locally or via cloud (e.g., MongoDB Atlas)
- **Redis** installed locally or via cloud (e.g., Redis Cloud)

### 1. Clone the Repository

```bash
git clone https://github.com/ifatoki/libra.git
cd libra
```

### 2. Set Up Virtual Environments

You will need two separate virtual environments for the frontend and backend APIs.

```bash
# For Frontend API
cd frontend-api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# For Backend API
cd ../backend-api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in both the **frontend** and **backend** directories with the following variables:

```bash
# MongoDB connection string
MONGO_URI=mongodb://localhost:27017/library

# Redis connection
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 4. Running the Services

To run the services locally:

#### Frontend API:

```bash
cd frontend
source venv/bin/activate
flask run --host=0.0.0.0 --port=5000
```

#### Backend API:

```bash
cd backend
source venv/bin/activate
flask run --host=0.0.0.0 --port=5001
```

The Frontend API will run on port `5000` and the Backend API on port `5001`.

## API Documentation

You can view details of the endpoints here https://documenter.getpostman.com/view/2602351/2sAXqtaLrS


## Running Unit Tests

The project uses `pytest` to run unit tests. Ensure that `pytest` is installed in your virtual environments.

### To run tests for the Frontend API:

```bash
cd frontend-api
source .venv/bin/activate
pytest
```

### To run tests for the Backend API:

```bash
cd backend-api
source .venv/bin/activate
pytest
```

## Event-Driven Approach

The system utilizes an event-driven architecture powered by Redis. Events such as user enrollment, book addition, book deletion, and book borrowing trigger notifications and updates across the microservices.

### Example Events:
- **User Enrollment**: Publishes a `user_enrolled` event.
- **Book Added**: Publishes a `book_added` event.
- **Book Deleted**: Publishes a `book_deleted` event.
- **Book Borrowed**: Publishes a `book_borrowed` event.

The Frontend API publishes events to a Redis channel (e.g., `frontend_events`), and the Backend API subscribes to these events to keep the systems in sync.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change. Make sure to update tests as appropriate.

## Contact

- Author: Itunuloluwa Fatoki
- GitHub: [ifatoki](https://github.com/ifatoki)
