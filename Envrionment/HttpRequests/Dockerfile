FROM python:3.11-slim

WORKDIR /app

RUN pip install requests aiohttp numpy redis apscheduler

COPY curl.py /scripts/

CMD ["python", "/scripts/curl.py"]
