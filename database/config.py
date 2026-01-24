DB_CONFIG = {
    "host": "localhost",
    "user": "presenceapp",
    "password": "presenceapp",
    "auth_plugin": "mysql_native_password",
    "ssl_disabled": True
}

REDIS_URL = "redis://localhost:6379/0"

CELERY_CONFIG = {
    "broker_url": REDIS_URL,
    "result_backend": REDIS_URL,
    "task_serializer": "json",
    "accept_content": ["json"],
}
