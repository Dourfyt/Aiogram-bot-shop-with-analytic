FROM python:3-slim

ENV PYTHONDONTWRITEBYTECODE=1

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN python -m pip install -r requirements.txt
RUN useradd -ms /bin/bash admin

WORKDIR /app
COPY . /app

RUN chown -R admin:admin /app
RUN chmod 755 /app
USER admin

CMD ["python", "app.py"]
