from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # 200 MB upload limit

limiter = Limiter(get_remote_address, app=app, default_limits=["20 per minute"])

from routes import bp  # import after `limiter` so routes.py can do `from app import limiter`

app.register_blueprint(bp)

if __name__ == "__main__":
    app.run(debug=False, port=5000)