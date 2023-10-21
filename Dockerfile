FROM python:3.11-alpine

RUN apk update \
    && apk add postgresql-dev gcc python3-dev musl-dev linux-headers
COPY . .
RUN pip3 install -r requirements.txt
WORKDIR /Matcha
CMD ["gunicorn", "-b", "0.0.0.0:8080", "-w", "1", "--timeout=180", "main:app"]