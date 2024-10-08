import os

class Config:
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/backend_library')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

class TestingConfig(Config):
    TESTING = True
    MONGO_URI = "mongomock://localhost"
    REDIS_URL = "redis://localhost:6379/0"
