import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
import requests
from datetime import datetime, timedelta
from functools import wraps
from bson.objectid import ObjectId



app = Flask(__name__)
app.secret_key = "xxxxxxx"
bcrypt = Bcrypt(app)



# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client.workout_planner
users_collection = db.users
history_collection = db.history  # Collection for workout history
metrics_collection = db.metrics  # Collection for health metrics


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

    # API request to API Ninjas
    api_url = f'https://api.api-ninjas.com/v1/exercises?muscle={muscle}&difficulty={difficulty}'
    headers = {'X-Api-Key': 'xxxxxxx'}

    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        exercises = response.json()
        return render_template('workout.html', exercises=exercises)
    else:
        return f"Error: Unable to fetch workout data. Status code: {response.status_code}"


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
        api_url = f'https://api.spoonacular.com/recipes/complexSearch?query={query}&addRecipeNutrition=true&apiKey=xxxxxx'

        response = requests.get(api_url)

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
    app.run(debug=True)
