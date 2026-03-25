from flask import Flask, request, render_template, send_from_directory, redirect
import os
from downloader import UniversalDownloader

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

downloader = UniversalDownloader(DOWNLOAD_FOLDER)

@app.route("/")
def index():
    files = os.listdir(DOWNLOAD_FOLDER)
    return render_template("index.html", files=files)

@app.route("/download", methods=["POST"])
def download_route():
    url = request.form.get("url")
    format_type = request.form.get("format")

    if not url:
        return redirect("/")

    try:
        if format_type == "mp3":
            downloader.download(url, "audio")
        else:
            downloader.download(url, "video")
    except Exception as e:
        print(e)

    return redirect("/")

@app.route("/files/<filename>")
def files(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename)

@app.route("/delete/<filename>")
def delete(filename):
    path = os.path.join(DOWNLOAD_FOLDER, filename)
    if os.path.exists(path):
        os.remove(path)
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)