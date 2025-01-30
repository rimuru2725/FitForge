# FitForge 🏋️‍♂️

**FitForge** is a dynamic workout planner designed to provide users with personalized workout plans, track their progress, and log their exercise history—all wrapped in a sleek, dark-themed web application.

---

## 📋 **Features**

1. **Personalized Workout Generator**  
   - Generates custom workout plans based on user input (e.g., muscle group, difficulty).  
   - Fetches exercises dynamically using the **API Ninjas Exercise API**.  

2. **Physical Health Metrics Tracking**  
   - Track your daily physical health metrics (e.g., Calorie consumed, Calorie Burned, Steps walked, etc).  
   - Track them on a weekly basis by vieweing on a line chart.

3. **Personalized Recipe Generation**  
   - Generates  recipes based on ingredients available (e.g., potato, tomato).  
   - Also generates the caloric information about the recipe including the calories and other macros.   
   - Fetches recipes with visuals dynamically using the **Spoonacular API**.  

4. **Workout Logging**  
   - Log details of your workouts, including muscle groups, exercises, weights, and reps.  
   - Update or modify previously logged workouts.  

5. **Workouts Tracking**  
   - Displays logged workouts over the past 7 days .
   - Helps user in Progressive Overloading.  

6. **User Authentication**  
   - Secure login and registration system for personalized user accounts.  

7. **Workout plans**  
   - Access our pre made workout plans based on some of the popular workout splits. 

8. **Aesthetic UI/UX**  
   - Dark theme with visually appealing Bootstrap.  
   - Clean layout for seamless user experience.  

---

## 🛠️ **Technologies Used**

- **Frontend**: HTML, CSS, JavaScript, Bootstrap 
- **Backend**: Python (Flask Framework)  
- **Database**: MongoDB  
- **API**: API Ninjas Exercise API, Spoonacular API. 

---

## Screenshots

### 1. Welcome Page
![Welcome Page](screenshots/welcome.png)

### 2. Login Page
![Login Page](screenshots/login.png)

### 3. Register Page
![Register Page](screenshots/register.png)

### 4. Home Page
![Home Page](screenshots/home.png)

### 5. Workout Generator
![Workout Generator](screenshots/workout_generator.png)

### 6. Workout Plans
![Workout Generator](screenshots/workout_plan1.png)

### 7. Workout plan
![Workout Generator](screenshots/workout_plan2.png)

### 8. Log Workout
![Log Workout](screenshots/workout_logging.png)

### 9. History Page
![History Page](screenshots/history.png)

### 10. Update Workout
![Update Workout](screenshots/update.png)

### 11. Log Your Physical Metrics Page
![Logging Physical Metrics Page](screenshots/metrics.png)

### 12. View Your Weekly Metrics Page
![View Metrics Page](screenshots/viewmetrics.png)

### 13. Recipe Generation Page
![Recipe Page](screenshots/recipes.png)




## Setup and Installation

1. Clone the repository
```bash
git clone https://github.com/rimuru2725/FitForge.git
cd fitforge
```

2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Create a .env file in the project root and add your environment variables:
```
SECRET_KEY=your_secret_key
MONGODB_URI=your_mongodb_uri
API_NINJAS_KEY=your_api_ninjas_key
SPOONACULAR_API_KEY=your_spoonacular_key
```

5. Run the application
```bash
python app.py
```

## Deployment

[Add deployment link when available]

## Author

[VIVEK]

## Acknowledgments

- API Ninjas for exercise data
- Spoonacular for recipe data

## 🤝 **Contributing**  
Contributions are always welcome! Feel free to open issues or submit pull requests.  

---

## 📧 **Contact**  
For any queries, reach out to:  
- **VIVEK**: [vivek27082005@gmail.com] 


## 📄 **License**  
This project is licensed under the [MIT License](LICENSE). 