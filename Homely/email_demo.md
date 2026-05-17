# Homely Email Demo Guide

This file explains how to demonstrate Homely's email-based features during the project demo.

The project currently supports two email-related flows:

1. Due-soon task reminder emails
2. Forgot-password reset emails

Both features use SMTP settings from environment variables. Credentials must not be committed to GitHub.

## Important Mailtrap Note

For the demo, we use Mailtrap Sandbox.

Mailtrap Sandbox captures outgoing emails inside the Mailtrap inbox. This means the email may not appear in a real personal Gmail/Outlook inbox. Instead, the expected demo behaviour is:

1. Homely sends the email using the configured SMTP settings.
2. Mailtrap receives and displays the email.
3. The reset/reminder email can be inspected inside the Mailtrap Sandbox inbox.

This is safer for a demo because it proves that Homely generated and sent the email without exposing real credentials or sending test messages to real users.

## Runtime Email Setup

From the `Homely` folder, activate the virtual environment:

```bash
source .venv/bin/activate
```

Set the Flask app and a local development secret key:

```bash
export FLASK_APP=Homely.py
export SECRET_KEY="dev-secret-key-for-testing-only"
```

Set the Mailtrap SMTP variables:

```bash
export EMAIL_REMINDERS_ENABLED=true
export EMAIL_REMINDERS_DRY_RUN=false
export MAIL_SERVER="sandbox.smtp.mailtrap.io"
export MAIL_PORT=2525
export MAIL_USE_TLS=true
export MAIL_USERNAME="YOUR_MAILTRAP_USERNAME"
export MAIL_PASSWORD="YOUR_MAILTRAP_SMTP_PASSWORD"
export MAIL_DEFAULT_SENDER="homely@example.com"
```

Do not put real Mailtrap credentials in:

- source code
- commits
- screenshots
- README examples
- pull request comments
- issue comments

## Starting the App for the Demo

From the `Homely` folder:

```bash
source .venv/bin/activate
export FLASK_APP=Homely.py
export SECRET_KEY="dev-secret-key-for-testing-only"

python -m flask db upgrade
python -m flask run --host=0.0.0.0 --port=5000
```

In GitHub Codespaces, open the forwarded port `5000`.

## Demo 1: Due-Task Email Reminders

Use this flow to demonstrate the task reminder feature.

1. Start the Flask app with the SMTP variables set.
2. Log in as a user.
3. Go to the dashboard.
4. Turn on email reminders using the opt-in button.
5. Create or assign a task to that user.
6. Set the task due date within the next 24 hours.
7. Click the manual send reminder email button.
8. Open the Mailtrap Sandbox inbox.
9. Confirm that a reminder email appears.

Expected result:

- the user must be opted in
- the task must be assigned to that user
- the task must be incomplete
- the task must be due within the reminder window
- the reminder email should appear in Mailtrap

The scheduled reminder job can also send reminders automatically while Flask is running, but the manual button is better for the live demo because it avoids waiting for the scheduled time.

## Demo 2: Forgot Password / Reset Password

Use this flow to demonstrate the password reset feature.

1. Start the Flask app with the SMTP variables set.
2. Open the login page.
3. Click `Forgot password?`.
4. Enter the email address for an existing Homely account.
5. Submit the form.
6. Open the Mailtrap Sandbox inbox.
7. Find the password reset email.
8. Copy the reset link from the email.
9. Open the reset link in the browser.
10. Enter a new password.
11. Submit the reset form.
12. Log in using the new password.

Expected result:

- the reset email appears in Mailtrap
- the reset link opens the reset-password page
- the user can set a new password
- the user can then log in with the new password

## Manual Reset Demo Without Real Email Delivery

If real SMTP sending is not available during the demo, use dry-run mode.

Set:

```bash
export EMAIL_REMINDERS_ENABLED=true
export EMAIL_REMINDERS_DRY_RUN=true
export FLASK_APP=Homely.py
export SECRET_KEY="dev-secret-key-for-testing-only"
```

Then start Flask:

```bash
python -m flask run --host=0.0.0.0 --port=5000
```

When the forgot-password form is submitted, the app should print the email body to the terminal instead of sending it. The reset link can be copied from the terminal output and opened in the browser.

This proves that the app can:

- generate a reset token
- create the reset-password link
- route the user to the reset form
- update the user's password

## Common Problems

### The login page shows a CSRF or secret-key error

Set a development secret key before running Flask:

```bash
export SECRET_KEY="dev-secret-key-for-testing-only"
```

Then restart the Flask server.

### The email does not appear in a personal inbox

This is expected if using Mailtrap Sandbox. Check the Mailtrap Sandbox inbox instead.

### The reminder email does not send

Check that:

- `EMAIL_REMINDERS_ENABLED=true`
- `EMAIL_REMINDERS_DRY_RUN=false`
- Mailtrap SMTP variables are set
- the user has opted in
- the task is assigned to that user
- the task is incomplete
- the task is due within the next 24 hours

### The reset email does not send

Check that:

- the email belongs to an existing Homely user
- Mailtrap SMTP variables are set
- `EMAIL_REMINDERS_ENABLED=true`
- `EMAIL_REMINDERS_DRY_RUN=false`
- the Mailtrap SMTP password is used, not the Mailtrap account login password

## Security Notes

- Do not commit real SMTP credentials.
- Do not commit `.env` files.
- Do not commit local `.db` files.
- Use environment variables for secrets.
- Password reset links are signed tokens and expire after the configured token lifetime.