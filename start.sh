PORT=34599

screen -d -m -S belka bash -c "source env.prod && \
			       source venv/bin/activate && \
			       gunicorn --bind=0.0.0.0:$PORT wsgi:slack_events_adapter.server"
