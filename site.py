from flask import Flask, render_template, request, redirect
from hunter import hunt_movies
import json
import os

app = Flask(__name__)

DATA_DIR = "data"
HISTORY_FILE = f"{DATA_DIR}/history.json"
SAVED_FILE = f"{DATA_DIR}/saved.json"

os.makedirs(DATA_DIR, exist_ok=True)


def save_json(path, obj):
    data = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    data.append(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


@app.route("/", methods=["GET", "POST"])
def index():
    results = []

    if request.method == "POST":
        name = request.form.get("name", "")
        year = request.form.get("year", "")
        filetype = request.form.get("filetype", ".mp4")

        results = hunt_movies(name, year, filetype)

        save_json(HISTORY_FILE, {
            "name": name,
            "year": year,
            "filetype": filetype
        })

    return render_template("index.html", results=results)


@app.route("/download")
def download():
    return redirect(request.args.get("url"))


@app.route("/save", methods=["POST"])
def save():
    save_json(SAVED_FILE, request.form.to_dict())
    return redirect("/")
    

if __name__ == "__main__":
    print("[SITE] Running at http://127.0.0.1:5000")
    app.run(debug=True, threaded=True)
