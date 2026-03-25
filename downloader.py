import yt_dlp

class UniversalDownloader:

    def get_direct_url(self, url):
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # نجيب رابط التحميل المباشر
            if 'url' in info:
                return info['url']

            if 'formats' in info:
                for f in info['formats']:
                    if f.get('ext') == 'mp4':
                        return f.get('url')

        return None