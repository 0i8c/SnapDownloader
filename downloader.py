import yt_dlp
import os

class UniversalDownloader:
    def __init__(self, download_path="downloads"):
        self.download_path = download_path
        os.makedirs(download_path, exist_ok=True)

    def download(self, url, mode="video"):
        if mode == "audio":
            ydl_opts = {
                'format': 'bestaudio',
                'outtmpl': f'{self.download_path}/%(title)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }],
            }
        else:
            ydl_opts = {
                'format': 'bestvideo+bestaudio/best',
                'outtmpl': f'{self.download_path}/%(title)s.%(ext)s',
                'merge_output_format': 'mp4',
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)