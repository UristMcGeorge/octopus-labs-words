FROM python:3.6
EXPOSE 8888
WORKDIR /app
ADD . /app
RUN pip install -r requirements.txt
CMD python words.py
