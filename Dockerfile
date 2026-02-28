FROM python:3.11-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 7860
CMD ["bash", "start.sh"]
