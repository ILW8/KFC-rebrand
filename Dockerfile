FROM ubuntu:22.04 AS backend
RUN export DEBIAN_FRONTEND=noninteractive &&  \
    apt-get update &&  \
    apt-get install -y  \
        python3-dev  \
        python3-pip  \
        default-libmysqlclient-dev  \
        build-essential \
        pkg-config
RUN pip install wheel
RUN pip install -U pip

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt && pip install uvicorn[standard]
COPY . /app

RUN python3 manage.py collectstatic --no-input

# gunicorn -k uvicorn.workers.UvicornWorker kfcrebrand.asgi:application -b 0.0.0.0:9727
# ~2-4 workers per core on a server
CMD ["gunicorn", "--workers", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:80", "kfcrebrand.asgi:application"]


FROM backend AS celery_worker
CMD ["celery", "-A", "kfcrebrand", "worker", "-l", "INFO"]


FROM ubuntu:22.04 AS statics_server
RUN apt-get update && apt-get install -y nginx && rm -v /etc/nginx/nginx.conf

COPY nginx.conf /etc/nginx/
COPY --from=backend /app/static /static

CMD ["nginx", "-g", "daemon off;"]

FROM fluentd:v1.16-1 AS fluentd_es
USER root
RUN ["gem", "install", "fluent-plugin-elasticsearch", "fluent-plugin-s3", "--no-document"]
USER fluent
