import os
import json
import certifi
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import requests
from datetime import datetime, timedelta
from functools import wraps
from bson.objectid import ObjectId
from dotenv import load_dotenv



app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
bcrypt = Bcrypt(app)




# MongoDB setup
client = MongoClient(os.getenv('MONGODB_URI'),server_api=ServerApi('1'))
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
    # Use environment variable for debug mode
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode)
