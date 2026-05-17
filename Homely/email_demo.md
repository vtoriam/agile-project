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

The Mailtrap username and password should only be set in the terminal or runtime environment. Do not add them to source code, commits, screenshots, pull request comments, or the README.

## How to Demo Email Reminders

1. Start the Flask app with the SMTP environment variables set.
2. Log in as a user.
3. Turn on email reminders using the dashboard opt-in button.
4. Create or assign a task to that user with a due date within the next 24 hours.
5. Use the dashboard manual send reminder button to send a reminder immediately.
6. Open the Mailtrap Sandbox inbox and show the received reminder email.

The scheduled reminder job can also send emails automatically while the Flask app is running, but the manual send button is easier for a live demo because it avoids waiting for the scheduled time.
