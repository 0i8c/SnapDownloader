from flask import Flask, request, jsonify, render_template
import requests
import os

app = Flask(__name__)

# الصفحة الرئيسية
@app.route("/")
def home():
    return render_template("index.html")

# API لفحص اليوزر
@app.route("/check")
def check():
    username = request.args.get("username")

    if not username:
        return jsonify({"status": "error", "message": "no username"})

    url = f"https://x.com/{username}"

    try:
        r = requests.get(url, timeout=5)

        if r.status_code == 404:
            return jsonify({"status": "available"})
        else:
            return jsonify({"status": "taken"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# تشغيل السيرفر (مهم لـ Render)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))