FROM python:3.6

RUN apt-get update && \
    apt-get install -y && \
    pip3 install uwsgi

COPY ./demo /opt/app
ADD . /opt/django_prepared_query
WORKDIR /opt/django_prepared_query
RUN python setup.py install

RUN pip3 install -r /opt/app/requirements

ENV DJANGO_ENV=prod
ENV DJANGO_SETTINGS_MODULE=demo.settings
ENV DOCKER_CONTAINER=1

WORKDIR /opt/app

CMD ["uwsgi", "--ini", "/opt/app/configs/uwsgi/uwsgi.ini"]