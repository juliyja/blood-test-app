FROM tiangolo/uwsgi-nginx-flask:python3.6 as build-stage
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
COPY src /app

FROM build-stage as dev-stage
COPY requirements-test.txt /tmp/requirements-test.txt
RUN pip install -r /tmp/requirements-test.txt
COPY tests /tests
CMD python main.py initdb \
    && python main.py run --port 8080 --host 0.0.0.0 --with-threads

FROM dev-stage as test-stage
ENV CODECOV_TOKEN "11f1d91f-90db-46ed-b188-cef7ea2f2293"
COPY .git .git
CMD python -m pytest --cov-report=xml --cov=. /tests && codecov

FROM build-stage
