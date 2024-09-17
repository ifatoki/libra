from app import app, r
from app.helpers.utils import handle_events


# Subscribe to the Redis event channel
pubsub = r.pubsub()
pubsub.subscribe(**{'backend_events': handle_events})

# Start the listener in a separate thread
pubsub.run_in_thread(sleep_time=0.001)

if __name__ == "__main__":
    app.run(debug=True, port=5001)

