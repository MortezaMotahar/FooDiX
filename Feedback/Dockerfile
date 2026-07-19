FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

ENV FLASK_ENV=production
ENV SECRET_KEY=default-secret-key-change-me
ENV ADMIN_USER=BlackHole
ENV ADMIN_PASS=Tesla369

CMD ["python", "app.py"]