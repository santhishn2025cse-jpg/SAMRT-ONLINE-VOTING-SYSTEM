import os
from pymongo import MongoClient
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
# Secret key is required to use Flask sessions securely
app.secret_key = 'super_secret_voting_key_dev' 

# Connect to MongoDB. Connects to localhost by default or parses MONGO_URI.
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URI)
db = client['voting_system']
votes_collection = db['votes']

# Predefined generic candidates for our online voting system
CANDIDATES = ['Python', 'JavaScript', 'Java', 'C++']

@app.route('/')
def home():
    # Main page is now the registration form
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    name = request.form.get('name')
    registration_no = request.form.get('registration_no')
    
    if not name or not registration_no or not registration_no.strip():
        return render_template('register.html', error="Both Name and Registration Number are required.")
    
    registration_no = registration_no.strip()
        
    # Check for existing vote to prevent double voting
    existing_vote = votes_collection.find_one({'registration_no': registration_no})
    if existing_vote:
        return render_template('register.html', error="This Registration Number has already been used to vote!")
            
    # Store registration info securely in the user's browser session
    session['name'] = name
    session['registration_no'] = registration_no
    
    # Redirect to the actual voting page now that they've passed verification
    return redirect(url_for('vote_page'))

@app.route('/vote', methods=['GET', 'POST'])
def vote_page():
    # If user tries to access /vote without registering first, redirect them back
    if 'registration_no' not in session:
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        candidate = request.form.get('candidate')
        registration_no = session.get('registration_no')
        name = session.get('name')
        
        if candidate in CANDIDATES:
            # Double check against duplicate vote to prevent race conditions
            if votes_collection.find_one({'registration_no': registration_no}):
                session.clear()
                return render_template('register.html', error="Duplicate vote attempted! Registration already used.")
                
            # Insert vote into MongoDB including the Name and Reg No
            votes_collection.insert_one({
                'name': name,
                'registration_no': registration_no,
                'candidate': candidate
            })
            
            # Clear session so they cannot refresh and post again easily
            session.clear()
            return redirect(url_for('results'))
            
    # GET request - Show the voting ballot
    return render_template('index.html', candidates=CANDIDATES, name=session.get('name'))

@app.route('/results')
def results():
    # Count votes for each candidate using MongoDB aggregation
    pipeline = [
        {"$group": {"_id": "$candidate", "count": {"$sum": 1}}}
    ]
    vote_data = list(votes_collection.aggregate(pipeline))
    
    # Map query results into a dictionary
    results_dict = {item['_id']: item['count'] for item in vote_data}
    
    # Ensure every candidate is shown in the results, even if they have 0 votes
    final_results = {c: results_dict.get(c, 0) for c in CANDIDATES}
    total_votes = sum(final_results.values())
    
    return render_template('results.html', results=final_results, total_votes=total_votes)

if __name__ == '__main__':
    # Debug mode should be true for local development
    app.run(debug=True)
