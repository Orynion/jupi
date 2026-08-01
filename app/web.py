from flask import Flask, request
from app.core.brain import think

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def home():
    response = ""

    if request.method == "POST":
        message = request.form["message"]
        response = think(message)

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI or is it?</title>
    </head>

    <body>
        <h1>AI or is it? 🤖</h1>

        <form method="post">
            <input name="message" placeholder="Talk to me...">
            <button type="submit">Send</button>
        </form>

        <p>AI: {response}</p>
    </body>
    </html>
    """


if __name__ == "__main__":
    app.run(debug=True)