FROM python:3.11-slim

WORKDIR /app
RUn apt update && apt-get install -y docker.io
RUN pip install -r requirements.txt

COPY . /app
EXPOSE 8000

CMD ["fastapi", "run", "main.py"]
