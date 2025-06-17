#!/bin/bash
set -e


if [ "$EXEC_ENV" != "docker" ]; then
  set -a               # экспортировать все переменные
  source .env          # загрузить .env
  set +a               # выключить автоэкспорт

  cd src
fi


case "$1" in
  bot-webhook)
    shift
    echo "Starting bot WEBHOOK..."
    exec poetry run gunicorn webhook_app:webhook_app --worker-class uvicorn.workers.UvicornWorker --bind $WEBHOOK_APP_HOST:$WEBHOOK_APP_PORT
    #exec poetry run gunicorn -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$CAPI_PORT control_api.api.control_api_app
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
