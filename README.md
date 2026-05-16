# Homely

Homely is a web application where a household can be created, household members can be added, and chores are transformed into a competitive to-do list with a leaderboard tracking points, as well as redeeming rewards with your points. Members can also steal points from other members if they complete tasks assigned to other people. Overdue tasks will result in a loss of points for each day it is late!
<br>

## Student Information:

| UWA ID   | Student Name   | GitHub Username |
| -------- | -------------- | --------------- |
| 24790172 | Victoria Mok   | vtoriam         |
| 24412257 | Isaac Foggin   | withFeathers    |
| 24193929 | Yamini Singh   | yamxnx          |
| 24033453 | Mohammad Saeed | Debravco        |

<br>

## How to run the application

Activate the virtual environment

`& .\venv\Scripts\Activate.ps1`

Install dependencies if needed

`pip install -r requirements.txt`

Start the Flask app

`flask --app Homely run`
<br><br>

## How to run tests

Run all unit tests

`pytest -q`

Run tests with warning details

`pytest -q -rw`

Run just the Selenium test file

`pytest tests/selenium_tests.py -q`
