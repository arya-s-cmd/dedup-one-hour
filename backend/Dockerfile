FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV DB_URL=sqlite:////data/app.db
ENV PYTHONUNBUFFERED=1
CMD ["bash", "-lc", "python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
