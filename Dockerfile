FROM python:3.7-alpine
ADD . /code
WORKDIR /code

RUN pip install redis
RUN pip install flask
RUN pip install flask_wtf
RUN pip install flask-bootstrap
RUN pip install flask-moment 

CMD python3 app.py

# docker build -t web .