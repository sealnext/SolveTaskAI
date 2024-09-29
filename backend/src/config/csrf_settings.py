from config import CSRF_SECRET_KEY, CSRF_TOKEN_EXPIRE_MINUTES

def get_csrf_config():
    return [
        ("secret_key", CSRF_SECRET_KEY),
        ("token_expire_minutes", CSRF_TOKEN_EXPIRE_MINUTES),
    ]

csrf_config = get_csrf_config