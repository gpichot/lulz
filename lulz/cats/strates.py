
import re
import urllib
import json
from BeautifulSoup import BeautifulSoup
from embed_video.backends import detect_backend, UnknownBackendException

"""
Detecter :
    - YouTube
    - DailyMotion
    - Vimeo
    - SoundClound
    - 9Gag
"""

class Detecter(object):
    def __init__(self, url):
        self.url = url
        self.is_valid = self.re_detect.match(url)

    def get(self):
        raise NotImplementedError

class SimpleImageDetecter(Detecter):
    re_detect = re.compile(r'^https?://.*\.(jpg|gif|png).*', re.I)

    def get(self):
        return {
            'type': 'image',
            'title': '',
            'description': '',
            'author': '',
            'thumbnail': self.url,
        }

class IMDB(Detecter):
    re_detect = re.compile(r'^(http(s)?://(www\.)?)?imdb\.com/title/.*', re.I)
    re_code = re.compile(r'/title/(?P<code>.*)/', re.I)

    def get(self):
        soup = BeautifulSoup(urllib.urlopen(self.url).read())

        bits = self.re_code.search(self.url)
        code = bits.group('code')
        iframe_code = """
            <iframe frameborder="0"  width="620" height="360" src="http://www.imdb.com/video/playlist/title?tconst=%s&amp;rid=undefined" scrolling="no" class="cboxIframe"></iframe>
        """ % code

        return {
            'type': 'image',
            'thumbnail': soup.find('meta', {'property': 'og:image', })['content'],
            'title': soup.find('meta', {'property': 'og:title', })['content'],
            'description': soup.find('meta', {'property': 'og:description'})['content'],
            'author': '',#soup.find('div', {'itemprop': 'director'}).a.span.content,
            'strate_name': 'IMDB',
            'strate_logo': 'imdb.png',
        }


class TheMovieDB(Detecter):
    re_detect = re.compile(r'^(http(s)?://(www\.)?)?themoviedb\.org/movie/.*', re.I)

    def get(self):
        soup = BeautifulSoup(urllib.urlopen(self.url).read())

        return {
            'type': 'image',
            'thumbnail': soup.find('meta', {'property': 'og:image', })['content'],
            'title': soup.find('meta', {'property': 'og:title', })['content'],
            'description': soup.find('meta', {'name': 'description'})['content'],
            'author': '',#soup.find('div', {'itemprop': 'director'}).a.span.content,
            'strate_name': 'TheMovieDB',
            'strate_logo': '',
        }


class TheMovieDBTv(Detecter):
    re_detect = re.compile(r'^(http(s)?://(www\.)?)?themoviedb\.org/tv/.*/season/\d+/episode/\d+', re.I)

    def get(self):
        soup = BeautifulSoup(urllib.urlopen(self.url).read())

        return {
            'type': 'image',
            'thumbnail': soup.find('img', {'class': 'lightbox', })['src'],
            'title': soup.find('h2', {'id': 'title', }).findAll('a')[1].text,
            'description': soup.find('div', {'id': 'mainCol'}).findAll('p')[1].text,
            'author': '',#soup.find('div', {'itemprop': 'director'}).a.span.content,
            'strate_name': 'TheMovieDB',
            'strate_logo': '',
        }


class DailyMotion(Detecter):
    re_detect = re.compile(r'^(http(s)?://(www\.)?)?dailymotion\.com/video/.*', re.I)
    re_code = re.compile(r'/video/(?P<code>[a-z0-9]+)_', re.I)

    url_api = 'https://api.dailymotion.com/video/%s?fields=title,description,id,thumbnail_240_url,embed_html'

    def get(self):
        bits = self.re_code.search(self.url)
        code = bits.group('code')
        data = json.loads(urllib.urlopen(self.url_api % code).read())

        return {
            'type': 'video',
            'thumbnail': data['thumbnail_240_url'],
            'title': data['title'],
            'description': data['description'],
            'author': '',
            'embed_video': data['embed_html'],
        }

class NineGag(Detecter):
    re_detect = re.compile(r'^(http(s)?://(www\.)?)?9gag\.com/gag/.*', re.I)

    def get(self):
        soup = BeautifulSoup(urllib.urlopen(self.url).read())

        return {
            'type': 'image',
            'thumbnail': soup.find('meta', {'property': 'og:image', })['content'],
            'title': soup.find('meta', {'property': 'og:title', })['content'],
            'description': '',
            'author': '',
            'strate_name': '9Gag',
            'strate_logo': '9gag.png',
        }
    

def detect_input(url):
    detecters = [SimpleImageDetecter, NineGag, DailyMotion, IMDB, TheMovieDB, TheMovieDBTv]

    for detecter in detecters:
        strate = detecter(url)
        print url
        print detecter
        if strate.is_valid:
            return strate.get()

    return None

def strate(url):

    data = {}

    # Youtube, Vimeo, SoundCloud
    try:
        video = detect_backend(url)
    except UnknownBackendException:
        pass
    else:
        data = {
            'type': 'video',
            'thumbnail': video.thumbnail,
            'title': video.title,
            'description': video.description,
            'author': video.author,
            'embed_video': video.get_embed_code(),
            'strate_name': 'YouTube',
            'strate_logo': 'youtube.png',
        }

    d = detect_input(url)
    if d is not None:
        data = d

    return data
