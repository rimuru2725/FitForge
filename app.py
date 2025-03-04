import os
import json
import certifi
import urllib.parse
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import requests
import urllib.parse
from datetime import datetime, timedelta
from functools import wraps
from bson.objectid import ObjectId
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
bcrypt = Bcrypt(app)


# MongoDB setup
mongodb_username = os.getenv('MONGODB_USERNAME')
mongodb_password = os.getenv('MONGODB_PASSWORD')

# URL encode the username and password
encoded_username = urllib.parse.quote_plus(mongodb_username)
encoded_password = urllib.parse.quote_plus(mongodb_password)

# Reconstruct the connection string with encoded credentials
connection_string = f"mongodb+srv://{encoded_username}:{encoded_password}@fitforge.ltei2.mongodb.net/?retryWrites=true&w=majority&appName=FitForge"

# Create MongoDB client
client = MongoClient(connection_string, server_api=ServerApi('1'))
db = client.workout_planner
users_collection = db.users
history_collection = db.history
metrics_collection = db.metrics
workout_plans_collection = db.workout_plans


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash("You need to log in first.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/home')
@login_required
def home():
    return render_template('home.html')


@app.route('/logout')
def logout():
    session.clear()  # Clear all session data
    return redirect('/')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if username exists
        if users_collection.find_one({"username": username}):
            flash("Username already exists!")
            return redirect(url_for('register'))

        # Hash the password and store the user
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        users_collection.insert_one({"username": username, "password": hashed_password})
        flash("Registration successful! Please log in.")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if user exists
        user = users_collection.find_one({"username": username})
        if user and bcrypt.check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])  # Store user ID in session
            session['username'] = username
            return redirect('/home')
        else:
            flash("Invalid credentials, please try again.")
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/generate-workout', methods=['POST'])
@login_required
def generate_workout():
    muscle = request.form['muscle']
    difficulty = request.form['difficulty']

    # API request to API Ninjas using environment variable
    api_url = f'https://api.api-ninjas.com/v1/exercises?muscle={muscle}&difficulty={difficulty}'
    headers = {'X-Api-Key': os.getenv('API_NINJAS_KEY')}

    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        exercises = response.json()
        return render_template('workout.html', exercises=exercises)
    else:
        return f"Error: Unable to fetch workout data. Status code: {response.status_code}"

    


@app.route('/api/workout-plans/<split_type>')
@login_required
def get_workout_plan(split_type):
    # Define workout plans for different splits
    plans = {
        "ppl": {
            "name": "Push Pull Legs",
            "frequency": "6 days per week",
            "description": "A balanced split targeting push muscles, pull muscles, and legs on separate days",
            "split": [
                {
                    "day": "Push Day",
                    "exercises": [
                        {"name": "Bench Press", "sets": "4", "reps": "8-12", "notes": "Focus on chest engagement"},
                        {"name": "Overhead Press", "sets": "3", "reps": "8-12", "notes": "Keep core tight"},
                        {"name": "Incline Dumbbell Press", "sets": "3", "reps": "10-12", "notes": "Control the negative"},
                        {"name": "Lateral Raises", "sets": "3", "reps": "12-15", "notes": "Light weight, perfect form"},
                        {"name": "Tricep Pushdowns", "sets": "3", "reps": "12-15", "notes": "Keep elbows tucked"}
                    ]
                },
                {
                    "day": "Pull Day",
                    "exercises": [
                        {"name": "Barbell Rows", "sets": "4", "reps": "8-12", "notes": "Keep back straight"},
                        {"name": "Pull-ups/Lat Pulldowns", "sets": "3", "reps": "8-12", "notes": "Full range of motion"},
                        {"name": "Face Pulls", "sets": "3", "reps": "12-15", "notes": "Focus on rear delts"},
                        {"name": "Bicep Curls", "sets": "3", "reps": "12-15", "notes": "No swinging"},
                        {"name": "Hammer Curls", "sets": "3", "reps": "12-15", "notes": "Control the movement"}
                    ]
                },
                {
                    "day": "Legs Day",
                    "exercises": [
                        {"name": "Squats", "sets": "4", "reps": "8-12", "notes": "Break parallel"},
                        {"name": "Romanian Deadlifts", "sets": "3", "reps": "8-12", "notes": "Feel the hamstrings"},
                        {"name": "Leg Press", "sets": "3", "reps": "10-12", "notes": "Full range of motion"},
                        {"name": "Calf Raises", "sets": "4", "reps": "15-20", "notes": "Squeeze at the top"},
                        {"name": "Leg Extensions", "sets": "3", "reps": "12-15", "notes": "Control the negative"}
                    ]
                }
            ]
        },
        "bro": {
            "name": "Bro Split",
            "frequency": "5 days per week",
            "description": "Traditional bodybuilding split focusing on one muscle group per day",
            "split": [
                {
                    "day": "Chest Day",
                    "exercises": [
                        {"name": "Flat Bench Press", "sets": "4", "reps": "8-12", "notes": "Wide grip"},
                        {"name": "Incline Dumbbell Press", "sets": "3", "reps": "8-12", "notes": "Feel the upper chest"},
                        {"name": "Cable Flyes", "sets": "3", "reps": "12-15", "notes": "Squeeze at the center"},
                        {"name": "Dips", "sets": "3", "reps": "10-12", "notes": "Lean forward for chest focus"}
                    ]
                },
                {
                    "day": "Back Day",
                    "exercises": [
                        {"name": "Deadlifts", "sets": "4", "reps": "6-8", "notes": "Keep back straight"},
                        {"name": "Pull-ups", "sets": "3", "reps": "8-12", "notes": "Wide grip"},
                        {"name": "Barbell Rows", "sets": "3", "reps": "10-12", "notes": "Squeeze shoulder blades"},
                        {"name": "Lat Pulldowns", "sets": "3", "reps": "12-15", "notes": "Feel the lats stretch"}
                    ]
                },
                {
                    "day": "Shoulder Day",
                    "exercises": [
                        {"name": "Military Press", "sets": "4", "reps": "8-10", "notes": "Keep core tight"},
                        {"name": "Lateral Raises", "sets": "4", "reps": "12-15", "notes": "Control the movement"},
                        {"name": "Front Raises", "sets": "3", "reps": "12-15", "notes": "Alternate arms"},
                        {"name": "Face Pulls", "sets": "3", "reps": "15-20", "notes": "High reps for rear delts"}
                    ]
                },
                
                {
                    "day": "Arms Day",
                    "exercises": [
                        {"name": "Barbell Curls", "sets": "4", "reps": "8-12", "notes": "Keep elbows fixed"},
                        {"name": "Skull Crushers", "sets": "4", "reps": "8-12", "notes": "Don't flare elbows"},
                        {"name": "Hammer Curls", "sets": "3", "reps": "10-12", "notes": "Focus on brachialis"},
                        {"name": "Tricep Pushdowns", "sets": "3", "reps": "12-15", "notes": "Keep elbows at sides"},
                        {"name": "Incline Dumbbell Curls", "sets": "3", "reps": "12-15", "notes": "Full range of motion"},
                        {"name": "Overhead Tricep Extension", "sets": "3", "reps": "12-15", "notes": "Keep elbows close"},
                        {"name": "21s Bicep Curls", "sets": "3", "reps": "21", "notes": "7 lower half, 7 upper half, 7 full range"}
                    ]
                },
                {
                    "day": "Legs Day",
                    "exercises": [
                        {"name": "Barbell Squats", "sets": "4", "reps": "8-10", "notes": "Break parallel"},
                        {"name": "Romanian Deadlifts", "sets": "4", "reps": "8-12", "notes": "Focus on hamstrings"},
                        {"name": "Leg Press", "sets": "3", "reps": "10-12", "notes": "Don't lock knees"},
                        {"name": "Walking Lunges", "sets": "3", "reps": "12/leg", "notes": "Keep torso upright"},
                        {"name": "Leg Extensions", "sets": "3", "reps": "12-15", "notes": "Squeeze quads at top"},
                        {"name": "Leg Curls", "sets": "3", "reps": "12-15", "notes": "Control the negative"},
                        {"name": "Standing Calf Raises", "sets": "4", "reps": "15-20", "notes": "Full range of motion"}
                    ]
                }
            ]
        },
        "full": {
                "name": "Full Body Split",
                "frequency": "3 days per week",
                "description": "Complete body workout focusing on compound movements and major muscle groups in each session",
                "split": [
                   {
            "day": "Full Body A",
            "exercises": [
                {"name": "Barbell Squats", "sets": "4", "reps": "8-10", "notes": "Focus on depth and form"},
                {"name": "Bench Press", "sets": "4", "reps": "8-12", "notes": "Control the negative"},
                {"name": "Bent Over Rows", "sets": "3", "reps": "8-12", "notes": "Keep back straight"},
                {"name": "Overhead Press", "sets": "3", "reps": "8-12", "notes": "Maintain tight core"},
                {"name": "Romanian Deadlifts", "sets": "3", "reps": "10-12", "notes": "Feel hamstring stretch"},
                {"name": "Lateral Raises", "sets": "3", "reps": "12-15", "notes": "Light weight, strict form"},
                {"name": "Plank", "sets": "3", "reps": "30-45 sec", "notes": "Keep body straight"}
            ]
                  },
        {
            "day": "Full Body B",
            "exercises": [
                {"name": "Deadlifts", "sets": "4", "reps": "6-8", "notes": "Maintain neutral spine"},
                {"name": "Incline Dumbbell Press", "sets": "4", "reps": "8-12", "notes": "Focus on upper chest"},
                {"name": "Pull-ups/Lat Pulldowns", "sets": "3", "reps": "8-12", "notes": "Full range of motion"},
                {"name": "Dumbbell Shoulder Press", "sets": "3", "reps": "8-12", "notes": "Control throughout"},
                {"name": "Leg Press", "sets": "3", "reps": "10-12", "notes": "Feet shoulder-width apart"},
                {"name": "Face Pulls", "sets": "3", "reps": "12-15", "notes": "Pull to forehead level"},
                {"name": "Cable Crunches", "sets": "3", "reps": "12-15", "notes": "Squeeze abs at bottom"}
            ]
        },
        {
            "day": "Full Body C",
            "exercises": [
                {"name": "Front Squats", "sets": "4", "reps": "8-10", "notes": "Keep elbows high"},
                {"name": "Dips", "sets": "3", "reps": "8-12", "notes": "Control descent"},
                {"name": "Barbell Rows", "sets": "3", "reps": "8-12", "notes": "Squeeze shoulder blades"},
                {"name": "Arnold Press", "sets": "3", "reps": "10-12", "notes": "Rotate dumbbells smoothly"},
                {"name": "Bulgarian Split Squats", "sets": "3", "reps": "10-12/side", "notes": "Keep front knee aligned"},
                {"name": "Chin-ups", "sets": "3", "reps": "8-12", "notes": "Supinated grip"},
                {"name": "Russian Twists", "sets": "3", "reps": "20/side", "notes": "Keep feet off ground"}
            ]
        }
    ]
    }
    
    }
    
    return jsonify(plans.get(split_type, {"error": "Split not found"}))
    
    

@app.route('/log-workout', methods=['GET', 'POST'])
@login_required
def log_workout():
    if request.method == 'POST':
        muscle_group = request.form.get('muscle_group')
        exercises = request.form.getlist('exercise_name[]')
        weights = request.form.getlist('weight_used[]')
        reps = request.form.getlist('reps[]')

        # Structure the data
        workout_log = {
            'username': session['username'],
            'date': datetime.now().strftime('%Y-%m-%d'),
            'muscle_group': muscle_group,
            'exercises': [
                {'exercise_name': ex, 'weight': wt, 'reps': rp}
                for ex, wt, rp in zip(exercises, weights, reps)
            ],
        }

        # Insert into MongoDB
        history_collection.insert_one(workout_log)
        flash("Workout logged successfully!", "success")
        return redirect('/history')

    return render_template('log_workout.html')


@app.route('/history')
@login_required
def history():
    # Get the current date and calculate the date 7 days ago
    current_date = datetime.now()
    past_seven_days = current_date - timedelta(days=7)

    # Query the database for workouts specific to the logged-in user within the last 7 days
    workouts = list(history_collection.find({
        "username": session['username'],  # Filter by username
        "date": {"$gte": past_seven_days.strftime('%Y-%m-%d')}
    }))

    # Convert MongoDB ObjectId and date fields to be JSON serializable
    for workout in workouts:
        workout['_id'] = str(workout['_id'])

    return render_template('history.html', workouts=workouts)


@app.route('/metrics', methods=['GET', 'POST'])
@login_required
def log_metrics():
    if request.method == 'POST':
        metrics_data = {
            'username': session['username'],
            'date': datetime.now().strftime('%Y-%m-%d'),
            'weight': request.form['weight'],
            'heart_rate': request.form['heart_rate'],
            'bp': request.form['bp'],
            'steps': request.form['steps'],
            'calories_burned': request.form['calories_burned'],
            'calories_consumed': request.form['calories_consumed'],
            'sleep_hours': request.form['sleep_hours'],
            'water_intake': request.form['water_intake'],
        }

        # Insert into MongoDB
        metrics_collection.insert_one(metrics_data)
        flash("Metrics logged successfully!", "success")
        return redirect('/metrics')

    return render_template('metrics.html')


@app.route('/metrics/view')
@login_required
def view_metrics():
    # Get the current date and calculate the date 7 days ago
    current_date = datetime.now()
    past_seven_days = current_date - timedelta(days=7)

    # Fetch metrics from the last 7 days for the logged-in user
    metrics = list(metrics_collection.find({
        "username": session['username'],
        "date": {"$gte": past_seven_days.strftime('%Y-%m-%d')}
    }))

    # Convert MongoDB ObjectId to string
    for metric in metrics:
        metric['_id'] = str(metric['_id'])

    return render_template('view_metrics.html', metrics=metrics)


@app.route('/recipes', methods=['GET', 'POST'])
@login_required
def recipes():
    if request.method == 'POST':
        query = request.form['query']
        api_url = f'https://api.spoonacular.com/recipes/complexSearch'
        params = {
            'query': query,
            'addRecipeNutrition': True,
            'apiKey': os.getenv('SPOONACULAR_API_KEY')
        }

        response = requests.get(api_url, params=params)

        if response.status_code == 200:
            recipes = response.json().get('results', [])
            for recipe in recipes:
                recipe['calories'] = recipe.get('nutrition', {}).get('nutrients', [{}])[0].get('amount', 'N/A')
                recipe['protein'] = next((n['amount'] for n in recipe.get('nutrition', {}).get('nutrients', []) if n['name'] == 'Protein'), 'N/A')
                recipe['fats'] = next((n['amount'] for n in recipe.get('nutrition', {}).get('nutrients', []) if n['name'] == 'Fat'), 'N/A')
                recipe['carbs'] = next((n['amount'] for n in recipe.get('nutrition', {}).get('nutrients', []) if n['name'] == 'Carbohydrates'), 'N/A')

            return render_template('recipes.html', recipes=recipes)
        else:
            flash("Failed to fetch recipes. Please try again.", "error")

    return render_template('recipes.html')

@app.route('/generate-meal-plan', methods=['POST'])
@login_required
def generate_meal_plan():
    target_calories = int(request.form['target_calories'])
    # Fix diet_type to match HTML form values
    diet_type = request.form['diet_type']
    
    # Map from HTML form value to backend value
    diet_map = {
        "vegetarian": "veg",
        "non-vegetarian": "non-veg"
    }
    
    backend_diet_type = diet_map.get(diet_type, "veg")
    
    # Predefined meal plans based on calories and diet type
    meal_plans = {
        "veg": {
            "1500": {
                "breakfast": [
                    {"name": "Oatmeal with Berries and Nuts", "calories": 350, "protein": 12, "carbs": 45, "fats": 14, "image": "/api/placeholder/400/300"},
                    {"name": "Greek Yogurt Parfait", "calories": 320, "protein": 15, "carbs": 40, "fats": 10, "image": "/api/placeholder/400/300"}
                ],
                "lunch": [
                    {"name": "Quinoa Salad with Chickpeas", "calories": 450, "protein": 15, "carbs": 60, "fats": 18, "image": "/api/placeholder/400/300"},
                    {"name": "Vegetable Wrap with Hummus", "calories": 420, "protein": 14, "carbs": 55, "fats": 15, "image": "/api/placeholder/400/300"}
                ],
                "dinner": [
                    {"name": "Stir-fried Tofu with Vegetables", "calories": 400, "protein": 20, "carbs": 30, "fats": 22, "image": "/api/placeholder/400/300"},
                    {"name": "Lentil Soup with Whole Grain Bread", "calories": 380, "protein": 18, "carbs": 50, "fats": 10, "image": "/api/placeholder/400/300"}
                ],
                "snacks": [
                    {"name": "Apple with Almond Butter", "calories": 200, "protein": 5, "carbs": 25, "fats": 10, "image": "/api/placeholder/400/300"},
                    {"name": "Vegetable Sticks with Guacamole", "calories": 150, "protein": 3, "carbs": 15, "fats": 10, "image": "/api/placeholder/400/300"}
                ]
            },
            "2000": {
                "breakfast": [
                    {"name": "Smoothie Bowl with Granola", "calories": 450, "protein": 15, "carbs": 65, "fats": 15, "image": "/api/placeholder/400/300"},
                    {"name": "Avocado Toast with Eggs", "calories": 480, "protein": 18, "carbs": 40, "fats": 28, "image": "/api/placeholder/400/300"}
                ],
                "lunch": [
                    {"name": "Buddha Bowl with Tahini Dressing", "calories": 550, "protein": 20, "carbs": 70, "fats": 22, "image": "/api/placeholder/400/300"},
                    {"name": "Vegetarian Burrito Bowl", "calories": 580, "protein": 22, "carbs": 75, "fats": 20, "image": "/api/placeholder/400/300"}
                ],
                "dinner": [
                    {"name": "Eggplant Parmesan with Salad", "calories": 520, "protein": 22, "carbs": 40, "fats": 30, "image": "/api/placeholder/400/300"},
                    {"name": "Veggie Stir Fry with Brown Rice", "calories": 480, "protein": 18, "carbs": 65, "fats": 18, "image": "/api/placeholder/400/300"}
                ],
                "snacks": [
                    {"name": "Protein Smoothie", "calories": 250, "protein": 20, "carbs": 25, "fats": 8, "image": "/api/placeholder/400/300"},
                    {"name": "Trail Mix", "calories": 200, "protein": 6, "carbs": 20, "fats": 12, "image": "/api/placeholder/400/300"}
                ]
            },
            "2500": {
                "breakfast": [
                    {"name": "Protein Pancakes with Fruit", "calories": 550, "protein": 25, "carbs": 70, "fats": 20, "image": "/api/placeholder/400/300"},
                    {"name": "Tofu Scramble with Vegetables", "calories": 520, "protein": 28, "carbs": 35, "fats": 30, "image": "/api/placeholder/400/300"}
                ],
                "lunch": [
                    {"name": "Falafel Wrap with Tahini Sauce", "calories": 650, "protein": 22, "carbs": 80, "fats": 28, "image": "/api/placeholder/400/300"},
                    {"name": "Quinoa Power Bowl", "calories": 680, "protein": 25, "carbs": 85, "fats": 25, "image": "/api/placeholder/400/300"}
                ],
                "dinner": [
                    {"name": "Vegetable Lasagna", "calories": 620, "protein": 25, "carbs": 65, "fats": 30, "image": "/api/placeholder/400/300"},
                    {"name": "Stuffed Bell Peppers with Rice", "calories": 580, "protein": 20, "carbs": 70, "fats": 25, "image": "/api/placeholder/400/300"}
                ],
                "snacks": [
                    {"name": "Protein Bar", "calories": 300, "protein": 20, "carbs": 30, "fats": 12, "image": "/api/placeholder/400/300"},
                    {"name": "Yogurt with Nuts and Honey", "calories": 280, "protein": 15, "carbs": 25, "fats": 15, "image": "/api/placeholder/400/300"}
                ]
            }
        },
        "non-veg": {
            "1500": {
                "breakfast": [
                    {"name": "Scrambled Eggs with Spinach", "calories": 320, "protein": 20, "carbs": 10, "fats": 22, "image": "/api/placeholder/400/300"},
                    {"name": "Greek Yogurt with Berries", "calories": 300, "protein": 18, "carbs": 35, "fats": 10, "image": "/api/placeholder/400/300"}
                ],
                "lunch": [
                    {"name": "Grilled Chicken Salad", "calories": 420, "protein": 35, "carbs": 20, "fats": 22, "image": "/api/placeholder/400/300"},
                    {"name": "Tuna Sandwich on Whole Grain", "calories": 450, "protein": 30, "carbs": 40, "fats": 18, "image": "/api/placeholder/400/300"}
                ],
                "dinner": [
                    {"name": "Baked Salmon with Vegetables", "calories": 450, "protein": 35, "carbs": 15, "fats": 25, "image": "/api/placeholder/400/300"},
                    {"name": "Turkey Meatballs with Zoodles", "calories": 380, "protein": 30, "carbs": 15, "fats": 20, "image": "/api/placeholder/400/300"}
                ],
                "snacks": [
                    {"name": "Protein Shake", "calories": 180, "protein": 25, "carbs": 10, "fats": 3, "image": "/api/placeholder/400/300"},
                    {"name": "Boiled Eggs", "calories": 140, "protein": 12, "carbs": 1, "fats": 10, "image": "/api/placeholder/400/300"}
                ]
            },
            "2000": {
                "breakfast": [
                    {"name": "Protein Oatmeal with Egg Whites", "calories": 450, "protein": 30, "carbs": 50, "fats": 15, "image": "/api/placeholder/400/300"},
                    {"name": "Turkey Bacon and Egg Muffins", "calories": 420, "protein": 35, "carbs": 20, "fats": 22, "image": "/api/placeholder/400/300"}
                ],
                "lunch": [
                    {"name": "Chicken and Quinoa Bowl", "calories": 550, "protein": 40, "carbs": 50, "fats": 20, "image": "/api/placeholder/400/300"},
                    {"name": "Salmon Poke Bowl", "calories": 520, "protein": 35, "carbs": 45, "fats": 22, "image": "/api/placeholder/400/300"}
                ],
                "dinner": [
                    {"name": "Lean Beef Stir Fry", "calories": 520, "protein": 40, "carbs": 30, "fats": 25, "image": "/api/placeholder/400/300"},
                    {"name": "Grilled Fish Tacos", "calories": 480, "protein": 35, "carbs": 40, "fats": 20, "image": "/api/placeholder/400/300"}
                ],
                "snacks": [
                    {"name": "Cottage Cheese with Fruit", "calories": 250, "protein": 25, "carbs": 20, "fats": 8, "image": "/api/placeholder/400/300"},
                    {"name": "Turkey and Avocado Roll-ups", "calories": 220, "protein": 20, "carbs": 5, "fats": 15, "image": "/api/placeholder/400/300"}
                ]
            },
            "2500": {
                "breakfast": [
                    {"name": "Steak and Eggs with Avocado", "calories": 580, "protein": 45, "carbs": 10, "fats": 40, "image": "/api/placeholder/400/300"},
                    {"name": "Protein Pancakes with Turkey Bacon", "calories": 620, "protein": 40, "carbs": 50, "fats": 25, "image": "/api/placeholder/400/300"}
                ],
                "lunch": [
                    {"name": "Chicken Caesar Wrap", "calories": 680, "protein": 50, "carbs": 40, "fats": 35, "image": "/api/placeholder/400/300"},
                    {"name": "Tuna Salad Stuffed Avocados", "calories": 650, "protein": 45, "carbs": 20, "fats": 45, "image": "/api/placeholder/400/300"}
                ],
                "dinner": [
                    {"name": "Grilled Steak with Sweet Potato", "calories": 680, "protein": 50, "carbs": 45, "fats": 30, "image": "/api/placeholder/400/300"},
                    {"name": "Salmon with Asparagus and Quinoa", "calories": 650, "protein": 45, "carbs": 40, "fats": 35, "image": "/api/placeholder/400/300"}
                ],
                "snacks": [
                    {"name": "Beef Jerky with Nuts", "calories": 320, "protein": 30, "carbs": 10, "fats": 20, "image": "/api/placeholder/400/300"},
                    {"name": "Protein Bar and Banana", "calories": 350, "protein": 25, "carbs": 40, "fats": 12, "image": "/api/placeholder/400/300"}
                ]
            }
        }
    }
    
    # Find closest calorie plan
    calorie_options = [1500, 2000, 2500]
    closest_cal = min(calorie_options, key=lambda x: abs(x - target_calories))
    closest_cal_str = str(closest_cal)
    
    # Get plan based on diet type and closest calorie option
    plan_data = meal_plans.get(backend_diet_type, {}).get(closest_cal_str, {})
    
    # If no exact match, default to a standard plan
    if not plan_data:
        flash("Couldn't find an exact meal plan match. Showing a standard plan.", "warning")
        plan_data = meal_plans["veg"]["2000"]  # Default plan
    
    # Format to match the expected structure in the template
    import random
    
    # Helper function to add missing fields
    def enhance_meal(meal):
        # Add description if not present
        if 'description' not in meal:
            descriptions = {
                'breakfast': [
                    "A nutritious start to your day with a perfect balance of proteins and carbs.",
                    "Kickstart your morning with this energy-packed meal."
                ],
                'lunch': [
                    "A satisfying midday meal to keep you going strong.",
                    "This balanced lunch provides sustained energy for the afternoon."
                ],
                'dinner': [
                    "A flavorful dinner that's both satisfying and nutritious.",
                    "End your day with this nutrient-rich meal that won't weigh you down."
                ],
                'snack': [
                    "A perfect between-meal boost to maintain energy levels.",
                    "This healthy snack will help you avoid unhealthy cravings."
                ]
            }
            
            # Find description based on meal name
            for meal_type, desc_list in descriptions.items():
                if meal_type in meal.get('name', '').lower():
                    meal['description'] = random.choice(desc_list)
                    break
            # Default description if none matched
            if 'description' not in meal:
                meal['description'] = "A balanced meal with optimal macronutrient distribution."
        
        # Add ingredients if not present
        if 'ingredients' not in meal:
            common_ingredients = {
                'Oatmeal': ['Rolled oats', 'Almond milk', 'Honey', 'Mixed berries', 'Chia seeds'],
                'Greek Yogurt': ['Greek yogurt', 'Honey', 'Granola', 'Fresh berries', 'Nuts'],
                'Smoothie': ['Banana', 'Spinach', 'Protein powder', 'Almond milk', 'Chia seeds'],
                'Pancakes': ['Whole grain flour', 'Eggs', 'Milk', 'Protein powder', 'Berries'],
                'Quinoa': ['Quinoa', 'Olive oil', 'Bell peppers', 'Cucumber', 'Cherry tomatoes'],
                'Salad': ['Mixed greens', 'Cherry tomatoes', 'Cucumber', 'Bell peppers', 'Olive oil'],
                'Wrap': ['Whole grain tortilla', 'Hummus', 'Cucumber', 'Tomatoes', 'Spinach'],
                'Bowl': ['Brown rice', 'Avocado', 'Black beans', 'Bell peppers', 'Lime juice'],
                'Tofu': ['Firm tofu', 'Soy sauce', 'Garlic', 'Broccoli', 'Bell peppers'],
                'Eggs': ['Eggs', 'Spinach', 'Cherry tomatoes', 'Feta cheese', 'Black pepper'],
                'Chicken': ['Chicken breast', 'Olive oil', 'Garlic powder', 'Mixed herbs', 'Lemon juice'],
                'Tuna': ['Canned tuna', 'Greek yogurt', 'Lemon juice', 'Dill', 'Red onion'],
                'Salmon': ['Salmon fillet', 'Lemon', 'Dill', 'Olive oil', 'Black pepper'],
                'Turkey': ['Ground turkey', 'Egg', 'Breadcrumbs', 'Italian herbs', 'Garlic powder'],
                'Beef': ['Lean beef', 'Garlic', 'Ginger', 'Soy sauce', 'Broccoli'],
                'Protein Shake': ['Protein powder', 'Almond milk', 'Banana', 'Ice', 'Cinnamon'],
                'Nuts': ['Almonds', 'Cashews', 'Walnuts', 'Dried cranberries', 'Dark chocolate chips'],
                'Bar': ['Dates', 'Oats', 'Protein powder', 'Nut butter', 'Dark chocolate chips'],
            }
            
            meal['ingredients'] = []
            for key, ingredients in common_ingredients.items():
                if key.lower() in meal.get('name', '').lower():
                    meal['ingredients'].extend(ingredients[:3])  # Add a few relevant ingredients
            
            # Add some generic ingredients if none matched
            if not meal['ingredients']:
                if 'veg' in backend_diet_type:
                    meal['ingredients'] = ['Mixed vegetables', 'Whole grains', 'Plant-based protein', 'Healthy fats', 'Herbs and spices']
                else:
                    meal['ingredients'] = ['Lean protein', 'Whole grains', 'Vegetables', 'Healthy fats', 'Herbs and spices']
        
        return meal
    
    # Create the formatted meal plan
    formatted_plan = {}
    
    # Select one meal of each type and enhance it
    for meal_type in ['breakfast', 'lunch', 'dinner', 'snacks']:
        meals = plan_data.get(meal_type, [])
        if meals:
            selected_meal = random.choice(meals)
            # For snacks, rename the key to match template
            key = 'snack' if meal_type == 'snacks' else meal_type
            formatted_plan[key] = enhance_meal(selected_meal.copy())
    
    # Calculate the total calories for the selected meal plan
    total_calories = 0
    total_protein = 0
    total_carbs = 0
    total_fats = 0
    
    for meal_key, meal in formatted_plan.items():
        total_calories += meal['calories']
        total_protein += meal['protein']
        total_carbs += meal['carbs']
        total_fats += meal['fats']
    
    # Add total nutrition to the formatted plan
    formatted_plan['total_calories'] = total_calories
    formatted_plan['total_protein'] = total_protein
    formatted_plan['total_carbs'] = total_carbs
    formatted_plan['total_fats'] = total_fats
    
    # Return to the recipes template with the meal plan data
    return render_template(
        'recipes.html', 
        meal_plan=formatted_plan,
        diet_type=diet_type,
        target_calories=target_calories,
        closest_calories=closest_cal,
        show_meal_plan=True
    )

@app.route('/delete/<entry_id>', methods=['POST'])
@login_required
def delete_entry(entry_id):
    history_collection.delete_one({"_id": ObjectId(entry_id), "username": session['username']})
    flash("Entry deleted successfully!", "success")
    return redirect('/history')


@app.route('/update/<entry_id>', methods=['GET', 'POST'])
@login_required
def update_entry(entry_id):
    if request.method == 'POST':
        updated_data = {
            "date": request.form['date'],
            "muscle_group": request.form['muscle_group'],
            "body_weight": request.form['body_weight'],
            "exercises": [
                {
                    "exercise_name": request.form['exercise_name'],
                    "weight": request.form['weight'],
                    "reps": request.form['reps']
                }
            ]
        }
        history_collection.update_one({"_id": ObjectId(entry_id), "username": session['username']}, {"$set": updated_data})
        flash("Entry updated successfully!", "success")
        return redirect('/history')

    entry = history_collection.find_one({"_id": ObjectId(entry_id), "username": session['username']})
    return render_template('update.html', entry=entry)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # Default to 10000 if PORT not set
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug_mode)

