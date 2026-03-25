from flask import Flask, request, render_template, redirect
import os
from downloader import UniversalDownloader

app = Flask(__name__)

downloader = UniversalDownloader()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download_route():
    url = request.form.get("url")

    if not url:
        return "❌ حط رابط"

    try:
        direct_url = downloader.get_direct_url(url)

        if not direct_url:
            return "❌ ما قدرنا نحصل رابط التحميل"

        # 🔥 هنا السر: نحول المستخدم مباشرة للرابط
        return redirect(direct_url)

    except Exception as e:
        return f"❌ خطأ: {e}"

if __name__ == "__main__":
    app.run(debug=True)