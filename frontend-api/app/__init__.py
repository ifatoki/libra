from flask import Flask
from flask_pymongo import PyMongo

# Initialize the app
app = Flask(__name__)

# Load the config
app.config.from_object('config.Config')

# Initialize MongoDB connection
mongo = PyMongo(app)

# Import routes (to be defined later)
from app import routes
