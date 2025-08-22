FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt
RUN cp config.example.yaml config.yaml
EXPOSE 8000

CMD ["fastapi", "run", "app.py"]
