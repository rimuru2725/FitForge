from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
import requests
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "xxxxxxxxxx"
bcrypt = Bcrypt(app)

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client.workout_planner
users_collection = db.users
history_collection = db['history']  # Collection for history


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/home')
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
            session['username'] = username
            return redirect('/home')
        else:
            return "Invalid Credentials, please try again"

    return render_template('login.html')


@app.route('/generate-workout', methods=['POST'])
def generate_workout():
    muscle = request.form['muscle']
    difficulty = request.form['difficulty']

    # API request to API Ninjas
    api_url = f'https://api.api-ninjas.com/v1/exercises?muscle={muscle}&difficulty={difficulty}'
    headers = {'X-Api-Key': 'xxxxxxxxx'}

    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        exercises = response.json()
        return render_template('workout.html', exercises=exercises)
    else:
        return f"Error: Unable to fetch workout data. Status code: {response.status_code}"


@app.route('/log-history', methods=['POST'])
def log_history():
    if 'username' not in session:
        return redirect('/login')

    # Collect data from the form
    workout = request.form['workout']
    sets = request.form['sets']
    weights = request.form['weights']
    bodyweight = request.form['bodyweight']
    date = datetime.now().strftime('%Y-%m-%d')

    # Insert into the database
    history_entry = {
        'username': session['username'],
        'date': date,
        'workout': workout,
        'sets': sets,
        'weights': weights,
        'bodyweight': bodyweight
    }

    history_collection.insert_one(history_entry)
    return redirect('/history')


@app.route('/history')
def history():
    # Get the current date and calculate the date 7 days ago
    current_date = datetime.now()
    past_seven_days = current_date - timedelta(days=7)

    # Query the database for workouts within the last 7 days
    workouts = list(history_collection.find({
        "date": {"$gte": past_seven_days.strftime('%Y-%m-%d')}  # Ensure string comparison
    }))

    # Convert MongoDB ObjectId and date fields to be JSON serializable
    for workout in workouts:
        workout['_id'] = str(workout['_id'])  # Convert ObjectId to string
        if 'date' in workout:
            workout['date'] = workout['date']  # Ensure date remains a string

    # Render the history page and pass the workouts data
    return render_template('history.html', workouts=workouts)

@app.route('/delete/<entry_id>', methods=['POST'])
def delete_entry(entry_id):
    from bson.objectid import ObjectId  # Import ObjectId for querying by MongoDB _id
    db.history.delete_one({"_id": ObjectId(entry_id)})
    return redirect('/history')


@app.route('/update/<entry_id>', methods=['GET', 'POST'])
def update_entry(entry_id):
    from bson.objectid import ObjectId
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
        db.history.update_one({"_id": ObjectId(entry_id)}, {"$set": updated_data})
        return redirect('/history')
    entry = db.history.find_one({"_id": ObjectId(entry_id)})
    return render_template('update.html', entry=entry)



@app.route('/log-workout', methods=['GET', 'POST'])
def log_workout():
    if 'username' not in session:
        return redirect('/login')

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

        return redirect('/history')

    return render_template('log_workout.html')


if __name__ == '__main__':
    app.run(debug=True)
