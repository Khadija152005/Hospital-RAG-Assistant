from apscheduler.schedulers.blocking import BlockingScheduler

from agents import CoordinatorAgent

from core import settings


def maintenance_job():

    print("\n Running scheduled maintenance workflow...\n")

    coordinator = CoordinatorAgent()

    result = coordinator.run()

    print("\n Workflow Summary:")
    print(result)



def run_scheduler():

    scheduler = BlockingScheduler()

    # TEST MODE
    # scheduler.add_job(
    #     maintenance_job,
    #     "interval",
    #     minutes=1,
    # )

    # PROD MODE every day at 8:00 AM
    scheduler.add_job(
        maintenance_job,
        "cron",
        hour=settings.CRON_TIME_HOUR,
        minute=settings.CRON_TIME_MINUTE
    )

    print(" Scheduler started...")

    scheduler.start()


# for testing purposes, you can run the scheduler directly
# run "python -m scheduler.scheduler"

if __name__ == "__main__":
    run_scheduler()