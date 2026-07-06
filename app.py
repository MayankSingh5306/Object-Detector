from extensions import app
from routes import bp 

app.register_blueprint(bp)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=7860)