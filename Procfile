web: cd src && python main.py initdb && gunicorn run:app --log-file -
worker: cd src && celery -A sender.tasks worker -B --loglevel info