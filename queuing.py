from flask import Flask, jsonify
from queue import Queue
from threading import Thread
import time

app = Flask(__name__)
task_queue = Queue()


def hello_world():
    time.sleep(3)  # Simulating a long-running task
    return "Hello, World!"


def process_queue():
    while True:
        task = task_queue.get()
        print("processing")
        task()
        task_queue.task_done()


@app.route("/")
def index():
    return "Hello, Flask Queue!"


@app.route("/hello")
def hello():
    task_queue.put(hello_world)
    return "Hello request queued!"


if __name__ == "__main__":
    # Start the background thread to process the queue
    worker = Thread(target=process_queue)
    worker.daemon = True
    worker.start()

    # Run the Flask app
    app.run(debug=True)
