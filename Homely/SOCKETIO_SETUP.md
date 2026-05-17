Install and run Socket.IO support

1. Install dependencies in your virtualenv:

```bash
pip install flask-socketio
# (optional) pin versions:
# pip install "flask-socketio==5.3.2" "python-socketio==5.9.0"
```

2. Run the app with Socket.IO (development):

```bash
$env:SECRET_KEY = "your secret key goes here"
python Homely.py
```

3. Notes:

- `Homely.py` now calls `socketio.run(app...)` so you should start the app with that file instead of `flask run`.
- The leaderboard client will join a household room and reload the page when a `leaderboard:update` event is received.
- For production, use an appropriate async worker (eventlet/gevent) and configure accordingly.
