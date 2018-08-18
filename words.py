import os
from collections import Counter
import tornado.ioloop
import tornado.web
import requests
from bs4 import BeautifulSoup
from bs4.element import Comment
import nltk
from database import prepare_database, add_words, get_words

settings = {
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
}


def tag_visible(element):
    """ Tag visible html elements."""
    if element.parent.name in [
        "style",
        "script",
        "head",
        "title",
        "meta",
        "[document]"
    ]:
        return False

    if isinstance(element, Comment):
        return False

    return True


def words_from_url(url):
    """ Fetch url's html, get visible elements' nouns and verbs, with
    counts.
    """
    pos_nouns = ("NN", "NNP", "NNS", "NNPS")
    pos_verbs = ("VB", "VBD", "VBG", "VBN", "VBP", "VBZ")

    try:  # TODO: handle redirects too
        try:
            r = requests.get(url)
        except requests.exceptions.MissingSchema:
            r = requests.get(f"http://{url}")
    except (
        requests.exceptions.InvalidURL,
        requests.exceptions.ConnectionError,
        requests.exceptions.ContentDecodingError,
    ):
        return False

    soup = BeautifulSoup(r.content, "html.parser")
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)
    visible_text_string = u" ".join(t.strip() for t in visible_texts)
    words = []
    for word, pos in nltk.pos_tag(nltk.word_tokenize(visible_text_string)):
        if len(word) < 2:  # get rid of the likes of 'c' and '/'
            continue
        if pos in pos_nouns+pos_verbs:
            words.append(word.lower())
    return Counter(words)


class MainHandler(tornado.web.RequestHandler):
    def both(self, message="", top_100_words=False):
        self.render(
            "templates/fetch.html",
            title="Words",
            message=message,
            top_100_words=top_100_words,
        )

    def get(self):
        self.both()

    def post(self):
        url = self.get_body_argument("url")
        words = words_from_url(url)
        top_100_words = False
        if words is False:  # empty list is handled below
            message = f"Error fetching {url}"
        else:
            try:
                top_word = words.most_common(1)[0][0]
                message = f"Fetched {url}, top word: {top_word}"
                top_100_words = words.most_common(100)
                add_words(url, top_100_words)
            except IndexError:
                message = f"Fetched {url}, it is empty"
        self.both(message, top_100_words)


class AdminHandler(tornado.web.RequestHandler):
    def get(self):
        all_words = get_words()
        self.render(
            "templates/show.html",
            title="Words",
            all_words=all_words,
        )


def make_app():
    return tornado.web.Application(
        [
            (r"/", MainHandler),
            (r"/admin/", AdminHandler)
        ],
        **settings,
    )


if __name__ == "__main__":
    prepare_database()
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
