from flask import Flask
from routes import bp

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024  # 200 MB upload limit

app.register_blueprint(bp)

if __name__ == "__main__":
    app.run(debug=False, port=5000)