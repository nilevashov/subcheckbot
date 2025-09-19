#!/bin/bash
set -e


if [ "$EXEC_ENV" != "docker" ]; then
  set -a               # экспортировать все переменные
  source .env          # загрузить .env
  set +a               # выключить автоэкспорт

  cd src
else
  set -a
  WEBHOOK_APP_HOST=0.0.0.0
  WEBHOOK_APP_PORT=5000
  set +a
fi

export PYTHONPATH="$PYTHONPATH:/opt/apps/subcheckbot/src"

case "$1" in
  bot-webhook)
    shift
    echo "Starting bot WEBHOOK..."
    exec poetry run gunicorn bot.webhook_app:webhook_app --worker-class uvicorn.workers.UvicornWorker --bind $WEBHOOK_APP_HOST:$WEBHOOK_APP_PORT
    ;;
  bot-polling)
    shift
    echo "Starting bot POLLING..."
    exec poetry run python run_polling.py
    ;;
  *)
    echo "Unknown service: $1"
    exec "$@"
    ;;
esac
