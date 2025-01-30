import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    MONGODB_URI = os.getenv('MONGODB_URI', 'your-mongodb-uri-here')
    API_NINJAS_KEY = os.getenv('API_NINJAS_KEY', 'your-api-ninjas-key-here')
    SPOONACULAR_API_KEY = os.getenv('SPOONACULAR_API_KEY', 'your-spoonacular-key-here')
    
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    DB_NAME = 'workout_planner'
    
    USERS_COLLECTION = 'users'
    HISTORY_COLLECTION = 'history'
    METRICS_COLLECTION = 'metrics'
    WORKOUT_PLANS_COLLECTION = 'workout_plans'