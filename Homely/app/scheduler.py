from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.email_utils import send_email


def deduct_overdue_points(app):
    with app.app_context():
        from app import db
        from app.models import Task, Membership

        now = datetime.now()

        # Find all incomplete overdue tasks that have an assigned user
        overdue_tasks = db.session.query(Task).filter(
            Task.is_completed == False,
            Task.due_date != None,
            Task.due_date < now,
            Task.assigned_user_id != None,
        ).all()

        for task in overdue_tasks:
            membership = db.session.query(Membership).filter_by(
                user_id=task.assigned_user_id,
                household_id=task.household_id,
            ).first()

            if membership:
                # Deduct 5 points but never go below zero
                membership.points = max(0, membership.points - 5)

        db.session.commit()
        print(f"[Scheduler] Deducted points for {len(overdue_tasks)} overdue tasks at {now}")



def format_due_task_email(user, tasks):
    """Create a readable due-soon reminder email body for one user."""
    task_lines = []

    for task in tasks:
        due_label = task.due_date.strftime("%a %d %b, %I:%M %p") if task.due_date else "No due date"
        task_lines.append(f"- {task.title} ({task.points_value} pts), due {due_label}")

    task_text = "\n".join(task_lines)

    return (
        f"Hi {user.display_name},\n\n"
        f"You have {len(tasks)} Homely task(s) due in the next 24 hours:\n\n"
        f"{task_text}\n\n"
        "Log in to Homely to complete them before they become overdue.\n"
    )


def send_due_task_email_reminders(app):
    """Send due-soon email reminders for incomplete tasks due in the next 24 hours.

    Real email sending is controlled by environment variables. By default this
    runs in dry-run mode so no credentials are needed for development/testing.
    """
    with app.app_context():
        from app import db
        from app.models import Task

        now = datetime.utcnow()
        window_end = now + timedelta(hours=24)

        due_tasks = (
            db.session.query(Task)
            .filter(
                Task.is_completed == False,
                Task.due_date != None,
                Task.due_date >= now,
                Task.due_date <= window_end,
                Task.assigned_user_id != None,
            )
            .order_by(Task.assigned_user_id.asc(), Task.due_date.asc())
            .all()
        )

        tasks_by_user = {}

        for task in due_tasks:
            if task.assignee and task.assignee.email:
                tasks_by_user.setdefault(task.assignee, []).append(task)

        sent_count = 0

        for user, tasks in tasks_by_user.items():
            subject = f"Homely reminder: {len(tasks)} task(s) due soon"
            body = format_due_task_email(user, tasks)

            if send_email(app, user.email, subject, body):
                sent_count += 1

        print(f"[Scheduler] Processed due-soon email reminders for {sent_count} user(s)")
        return sent_count

def start_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=deduct_overdue_points,
        trigger=CronTrigger(hour=0, minute=0),  # midnight every day
        args=[app],
        id="deduct_overdue_points",
        replace_existing=True,
    )
    scheduler.add_job(
        func=send_due_task_email_reminders,
        trigger=CronTrigger(hour=9, minute=0),  # 9am daily
        args=[app],
        id="send_due_task_email_reminders",
        replace_existing=True,
    )

    scheduler.start()
    print("[Scheduler] Started — overdue points deduction runs at midnight")
    return scheduler