from flask import render_template
from app import app

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Homely')

@app.route('/edit-profile')
def edit_profile():
    return render_template('edit-profile.html', title='Edit Profile')


@app.route('/rewards')
def rewards():
    return render_template('rewards.html', title='Rewards')