# Homely

Homely is a household management web application for shared households. It helps housemates manage chores, tasks, points, leaderboards, rewards, overdue tasks, and reminders in one place.

## Student Information

| UWA ID   | Student Name   | GitHub Username |
| -------- | -------------- | --------------- |
| 24790172 | Victoria Mok   | vtoriam         |
| 24412257 | Isaac Foggin   | withFeathers    |
| 24193929 | Yamini Singh   | yamxnx          |
| 24033453 | Mohammad Saeed | Debravco        |

## Main Features

- User accounts and login/logout
- Household creation and joining
- Dashboard showing household tasks and warnings
- My Tasks page for tasks assigned to the logged-in user
- Task creation, completion, and deletion
- Points system for completed tasks
- Leaderboard for household members
- Rewards page with claimable/custom rewards
- Overdue task warnings and point deductions
- Due-soon task reminders
- Optional email reminder support using SMTP/Mailtrap
- Unit tests and Selenium WebDriver tests

## Technology Stack

- Python
- Flask
- Jinja templates
- Flask-SQLAlchemy
- Flask-Migrate / Alembic
- SQLite
- Flask-Login
- Flask-WTF
- APScheduler
- Pytest
- Selenium WebDriver
- HTML, CSS, and JavaScript

## Running the Application in GitHub Codespaces, Linux, or macOS

From the repository root:

```bash
cd Homely
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

export FLASK_APP=Homely.py
python -m flask db upgrade
python -m flask run --host=0.0.0.0 --port=5000
```

In GitHub Codespaces, open the forwarded port `5000` to view the website.

## Running the Application on Windows PowerShell

From the repository root:

```powershell
cd Homely
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt

$env:FLASK_APP = "Homely.py"
py -m flask db upgrade
py -m flask run
```

Then open the local Flask URL shown in the terminal.

## Database Setup

The app uses Flask-Migrate/Alembic migrations.

From the `Homely` folder:

```bash
source .venv/bin/activate
export FLASK_APP=Homely.py
python -m flask db upgrade
```

If the local database becomes stale or has migration errors, delete the local SQLite database and rebuild it:

```bash
find . -type f -name "*.db" -delete
export FLASK_APP=Homely.py
python -m flask db upgrade
```

Do not commit local `.db` files.

## Running Tests

From the `Homely` folder:

```bash
source .venv/bin/activate
python -m pytest -q
```

Run only the email reminder tests:

```bash
python -m pytest tests/test_email_reminders.py -q
```

Run the Selenium tests:

```bash
python -m pytest tests/selenium_tests.py -q
```

## Email Reminder Behaviour

Email reminders are only sent when:

- SMTP settings are configured at runtime
- `EMAIL_REMINDERS_ENABLED=true`
- `EMAIL_REMINDERS_DRY_RUN=false`
- the user has opted in to email reminders
- the user has an incomplete task due within the reminder window
- the task is assigned to that user

Dry-run mode can be used for safe testing without sending real emails:

```bash
export EMAIL_REMINDERS_DRY_RUN=true
```

## Common Troubleshooting

### `no such table: user` or `no such table: task`

The local database probably has not been created or is stale.

Run from the `Homely` folder:

```bash
find . -type f -name "*.db" -delete
export FLASK_APP=Homely.py
python -m flask db upgrade
```

### Email reminders do not send

Check that:

- SMTP variables are set in the same terminal running Flask
- `EMAIL_REMINDERS_ENABLED=true`
- `EMAIL_REMINDERS_DRY_RUN=false`
- the user has opted in
- the task is assigned to that user
- the task is incomplete
- the task is due within the next 24 hours
- the Mailtrap password is the SMTP password, not the account login password
