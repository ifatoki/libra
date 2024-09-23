from flask import Flask
from flask_pymongo import PyMongo
import redis

# Initialize the app
app = Flask(__name__)

# Load the config
app.config.from_object("config.Config")

# Initialize MongoDB connection
mongo = PyMongo(app)

# Redis connection
r = redis.Redis.from_url(app.config["REDIS_URL"])

# Register blueprints
from app.routes import user_bp

app.register_blueprint(user_bp)
