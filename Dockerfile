FROM tiangolo/meinheld-gunicorn-flask:python3.7-alpine3.8

COPY ./app /app
COPY requirements.txt /app
WORKDIR /app
RUN pip install -r requirements.txt
