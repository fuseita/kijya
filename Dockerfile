FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN apt update && apt-get install -y docker.io && apt clean
RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["fastapi", "run", "main.py"]
