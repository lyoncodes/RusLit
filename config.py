class Config:
    DEBUG = True
    SECRET_KEY = 'your_secret_key_here'  # Change this to a random secret key
    TESTING = False

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    DEBUG = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False