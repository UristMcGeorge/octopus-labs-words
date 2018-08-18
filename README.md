# Octopus Labs Words

Webside scraper and words sorter for Octopus Labs

## Getting Started

Start and test:
docker-compose up
curl 127.0.0.1:8888

Use:
Point your browser to 127.0.0.1:8888, enter some URLs, go to 127.0.0.1:8888/admin/

Debug:
mysql --host 127.0.0.1 --port 3306 --user root --password words

Drop the database after each run, see TODO below.

## Built With

* [Tornado](http://www.tornadoweb.org/en/stable/) - The web framework used
* [MySQL-Python](http://mysql-python.sourceforge.net/) - Database adapter
* [Requests](http://docs.python-requests.org/en/master/) - HTTP for Humans
* [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) - HTML parser
* [Natural Language Toolkit](https://www.nltk.org/) - Language processor
* [PyNaCl](https://github.com/pyca/pynacl) - Networking and Cryptography library Python binding

## Authors

* George Georgiev - eorg@mail.bg

## TODO
- installable package
- paginate the admin
- persist the encryption key, currently we generate a new one every run
- more in code
