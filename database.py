from collections import OrderedDict
import MySQLdb
import nacl.pwhash
import nacl.utils
from nacl.public import PrivateKey, Box

# TODO: database configs in environment config files
connection = MySQLdb.connect(
    host="db",
    port=3306,
    user="root",
    passwd="root",
)

sk = PrivateKey.generate()
pk = sk.public_key
box = Box(sk, pk)


def prepare_database():
    """Create the database and the tables, if they don't exist already."""
    with connection as cursor:
        cursor.execute("""CREATE DATABASE IF NOT EXISTS words;""")
        cursor.execute("""USE words;""")
        # arbitrary url length limit, text can't be unique
        cursor.execute("""CREATE TABLE IF NOT EXISTS url (
            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            url VARCHAR(3072) NOT NULL UNIQUE
            );""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS word (
            hash BLOB NOT NULL,
            word BLOB NOT NULL,
            count INT NOT NULL,
            url_id INT NOT NULL,
            FOREIGN KEY (url_id) REFERENCES url(id)
            );""")


def prepare_words(words, url_id):
    """ Do the encryption stuff, prepare executemany friendly list.

    Args:
        words (collections.Counter): The words with their counts, sorted by
            count. Example: (('eggs': 5), ('spam': 3))
        url_id (int): The id of the just inserted url table row.

    Returns:
        prepared_words (list): executemany ready list.
    """
    prepared_words = []
    for word in words:
        # TODO: move the encryption parts to another file
        # TODO: persist the key, currently we generate a new one every run
        salted_hash = nacl.pwhash.str(word[0].encode("utf-8"))  # needs bytes
        encrypted_word = box.encrypt(word[0].encode("utf-8"))  # needs bytes
        count = word[1]
        prepared_words.append([
            salted_hash,
            encrypted_word,
            count,
            url_id
        ])
    return(prepared_words)


def add_words(url, words):
    """ Add URL and words to the database.

    Args:
        url (str): The URL.
        words (collections.Counter): The words with their counts, sorted by
            count. Example: (('eggs': 5), ('spam': 3))
    """
    url = url.lstrip('http://').lstrip('https://')  # TODO: non-naive
    with connection as cursor:
        cursor.execute("INSERT IGNORE INTO url (url) VALUES (%s);", (url,))
        cursor.execute("SELECT LAST_INSERT_ID();")
        url_id = cursor.fetchone()[0]
        if url_id == 0:  # already there
            cursor.execute("SELECT id FROM url WHERE url=(%s);", (url,))
            url_id = cursor.fetchone()[0]

        # use delete+insert instead of update, because if there are less words
        # on the second fetch we'll have leftovers
        # also the database engine does it anyway
        cursor.execute("DELETE FROM word WHERE url_id=%s;", (url_id,))
        prepared_words = prepare_words(words, url_id)
        cursor.executemany(
            """INSERT INTO word (hash, word, count, url_id)
            VALUES (%s, %s, %s, %s)""",
            prepared_words
        )


def get_words():
    all_words = {}
    with connection as cursor:
        # TODO: large set?
        cursor.execute("SELECT word, count FROM word;")
        words = cursor.fetchall()
        for word in words:
            decrypted_word = box.decrypt(word[0]).decode("utf-8")
            try:
                all_words[decrypted_word] += word[1]
            except KeyError:  # or defaultdict
                all_words[decrypted_word] = word[1]
    ordered_words = OrderedDict(sorted(
        all_words.items(),
        key=lambda x: x[1],
        reverse=True
    ))
    return ordered_words.keys()
