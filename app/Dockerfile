FROM python:3.10-alpine

RUN adduser flask -D

WORKDIR /home/flask

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY .. .

USER flask

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0", "--port=8080"]