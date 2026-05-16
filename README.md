# Homely

Homely is a household management web application for shared households. It helps housemates manage chores, tasks, points, leaderboards, rewards, overdue tasks, and reminders in one place.

The main idea is to make household responsibilities more visible and fair by combining a shared task board with gamified features such as points, rewards, and contribution tracking.

## Student Information

| UWA ID | Student Name | GitHub Username |
| ------ | ------------ | --------------- |
| 24790172 | Victoria Mok | vtoriam |
| 24412257 | Isaac Foggin | withFeathers |
| 24193929 | Yamini Singh | yamxnx |
| 24033453 | Mohammad Saeed | Debravco |

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
- SQLite for local development
- Flask-Login
- Flask-WTF
- APScheduler
- Pytest
- Selenium WebDriver
- HTML, CSS, and JavaScript

## Repository Structure

```text
Homely/
  Homely.py                  Flask entry point
  requirements.txt           Python dependencies
  app/
    __init__.py              Flask app factory and extensions
    models.py                Database models
    routes.py                Application routes
    scheduler.py             Scheduled jobs, including overdue deductions and email reminders
    email_utils.py           Email sending helper
    templates/               Jinja templates
    static/                  CSS, JavaScript, and images
  migrations/                Flask-Migrate/Alembic migrations
  tests/                     Pytest and Selenium tests
README.md
```

## Running the Application in GitHub Codespaces / Linux / macOS

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

Run this from the `Homely` folder:

```bash
source .venv/bin/activate
export FLASK_APP=Homely.py
python -m flask db upgrade
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
$env:FLASK_APP = "Homely.py"
py -m flask db upgrade
```

## Resetting the Local Database

If the local database becomes stale or has migration errors, delete the local SQLite database and rebuild it.

From the `Homely` folder on Codespaces/Linux/macOS:

```bash
find . -type f -name "*.db" -delete
export FLASK_APP=Homely.py
python -m flask db upgrade
```

On Windows PowerShell, delete the local `.db` file manually if it exists, then run:

```powershell
$env:FLASK_APP = "Homely.py"
py -m flask db upgrade
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

## Email Reminder Demo Setup

Email reminders use SMTP settings from environment variables. Credentials must not be committed to GitHub.

For a Mailtrap Sandbox demo, set these variables from the `Homely` folder:

```bash
source .venv/bin/activate

export EMAIL_REMINDERS_ENABLED=true
export EMAIL_REMINDERS_DRY_RUN=false
export MAIL_SERVER="sandbox.smtp.mailtrap.io"
export MAIL_PORT=2525
export MAIL_USE_TLS=true
export MAIL_USERNAME="YOUR_MAILTRAP_USERNAME"
export MAIL_PASSWORD="YOUR_MAILTRAP_SMTP_PASSWORD"
export MAIL_DEFAULT_SENDER="homely@example.com"
export FLASK_APP=Homely.py
```

For Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1

$env:EMAIL_REMINDERS_ENABLED = "true"
$env:EMAIL_REMINDERS_DRY_RUN = "false"
$env:MAIL_SERVER = "sandbox.smtp.mailtrap.io"
$env:MAIL_PORT = "2525"
$env:MAIL_USE_TLS = "true"
$env:MAIL_USERNAME = "YOUR_MAILTRAP_USERNAME"
$env:MAIL_PASSWORD = "YOUR_MAILTRAP_SMTP_PASSWORD"
$env:MAIL_DEFAULT_SENDER = "homely@example.com"
$env:FLASK_APP = "Homely.py"
```

The Mailtrap username and password should only be set in the terminal or environment. Do not add them to source code, README examples, commits, screenshots, or pull request comments.

## How to Demo Email Reminders

1. Start the Flask app with the SMTP environment variables set.
2. Log in as a user.
3. Turn on email reminders using the dashboard opt-in button.
4. Create or assign a task to that user with a due date within the next 24 hours.
5. Use the dashboard's manual send reminder button to send a reminder immediately.
6. Open the Mailtrap Sandbox inbox and show the received reminder email.

The scheduled reminder job can also send emails automatically while the Flask app is running, but the manual send button is easier for a live demo because it avoids waiting for the scheduled time.

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

### Flask cannot find the app

Make sure you are inside the `Homely` folder and have set:

```bash
export FLASK_APP=Homely.py
```

or on Windows PowerShell:

```powershell
$env:FLASK_APP = "Homely.py"
```

## Security Notes

- Do not commit `.env` files, database files, SMTP passwords, API keys, or Mailtrap credentials.
- Keep `SECRET_KEY`, SMTP credentials, and database URLs in environment variables.
- Local databases are for development/demo only and should not be committed.
