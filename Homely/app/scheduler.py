from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


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


def start_scheduler(app):
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=deduct_overdue_points,
        trigger=CronTrigger(hour=0, minute=0),  # midnight every day
        args=[app],
        id="deduct_overdue_points",
        replace_existing=True,
    )
    scheduler.start()
    print("[Scheduler] Started — overdue points deduction runs at midnight")
    return scheduler