FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn 


COPY . .

RUN chmod +x ./entrypoint.sh

ENV DJANGO_SETTINGS_MODULE=wa_router.settings 


EXPOSE 5000

CMD ["gunicorn", "fusionCart.wsgi:application", "--bind", "0.0.0.0:5000"] 