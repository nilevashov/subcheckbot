import os

from settings import config

if os.getenv("EXEC_ENV") == "docker":
    config.app_host = "0.0.0.0"
    config.app_port = 5000

bind = f"{config.app_host}:{config.app_port}"
worker_class = "uvicorn.workers.UvicornWorker"
