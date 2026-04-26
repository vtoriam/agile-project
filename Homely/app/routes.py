from flask import render_template
from app import app


@app.route('/index')
def index():
    return render_template('index.html', title='Homely')

@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html', title='Home')

@app.route('/leaderboard')
def leaderboard():
    return render_template('leaderboard.html', title='Leaderboard')

@app.route('/edit-profile')
def edit_profile():
    return render_template('edit-profile.html', title='Edit Profile')

@app.route('/rewards')
def rewards():
    return render_template('rewards.html', title='Rewards')
