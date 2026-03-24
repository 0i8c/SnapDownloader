from flask import Flask, request, render_template, send_from_directory, redirect
import os
import requests
import subprocess

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route("/")
def index():
    files = os.listdir(DOWNLOAD_FOLDER)
    return render_template("index.html", files=files)

@app.route("/download", methods=["POST"])
def download():
    url = request.form.get("url")
    format_type = request.form.get("format")

    if not url:
        return redirect("/")

    try:
        filename = url.split("/")[-1].split("?")[0]
        file_path = os.path.join(DOWNLOAD_FOLDER, filename)

        r = requests.get(url, stream=True)
        with open(file_path, "wb") as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)

        # 🎧 تحويل إلى MP3
        if format_type == "mp3":
            mp3_path = file_path + ".mp3"
            subprocess.run([
                "ffmpeg", "-i", file_path,
                "-q:a", "0", "-map", "a",
                mp3_path
            ])
            os.remove(file_path)

        return redirect("/")

    except Exception as e:
        return f"خطأ: {e}"

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