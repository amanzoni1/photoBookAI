from app import app
from routes import get_job_queue

with app.app_context():
    queue = get_job_queue()
    queue.reset_all_jobs()