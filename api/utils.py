# import random
import uuid
from django.contrib.auth import get_user_model

from api.models import ChatRoom


def generate_username_suggestions(base_name, count=5):
    User = get_user_model()
    suggestions = set()

    attempts = 0
    max_attempts = count * 10

    while len(suggestions) < count and attempts < max_attempts:
        random_number = uuid.uuid4().hex[:4]
        username = f"{base_name}_{random_number}"
        if not User.objects.filter(username=username).exists():
            suggestions.add(username)
        attempts += 1

    return list(suggestions)


def generate_random_titles(base_name, count=5):
    titles = set()

    attempts = 0
    max_attempts = count * 10

    while len(titles) < count and attempts < max_attempts:
        random_number = uuid.uuid4().hex[:4]
        title = f"{base_name}_{random_number}"
        if not ChatRoom.objects.filter(title=title).exists():
            titles.add(title)
        attempts += 1

    return list(titles)


def replace_existing_google_username(base_name):
    User = get_user_model()
    attempts = 0
    max_attempts = 50

    if not User.objects.filter(username=base_name).exists():
        return base_name

    while attempts < max_attempts:
        random_suffix = uuid.uuid4().hex[:4]
        username = f"{base_name}_{random_suffix}"
        if not User.objects.filter(username=username).exists():
            return username
        attempts += 1

    # Fallback if somehow all attempts fail
    return f"{base_name}_{uuid.uuid4().hex[:6]}"
