from flask import Flask app = Flask(name)
@app.route("/") def index(): return "Hello from Python on Render!"
if name == "main": app.run()
