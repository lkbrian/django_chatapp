FROM python:3.13-slim-bookworm

# ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN chmod +x /app/django.sh


EXPOSE 8000

CMD ["sh","/app/django.sh"]