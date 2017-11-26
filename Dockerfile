FROM python:alpine

COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt
COPY *.py /

CMD python /app.py
