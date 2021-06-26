FROM python:3.9.5-alpine

RUN apk add --no-cache postgresql-libs && \
    apk add --no-cache --virtual .build-deps \
        build-base \
        gcc \
        musl-dev \
        postgresql-dev && \
    pip install --upgrade pip &&\
    pip install pipenv

RUN echo "@edge http://dl-cdn.alpinelinux.org/alpine/edge/main" >> /etc/apk/repositories && \
    echo "@edgecommunity http://dl-cdn.alpinelinux.org/alpine/edge/community" >> /etc/apk/repositories && \
    apk add --no-cache alpine-sdk 'librdkafka@edgecommunity>=1.6.0' 'librdkafka-dev@edgecommunity>=1.6.0'

COPY ./ /app/

WORKDIR /app

RUN pipenv install -e .

RUN apk upgrade --force-broken-world && \
    apk add --no-cache libstdc++ && \
    apk --purge del .build-deps

EXPOSE 5000

ENTRYPOINT [ "pipenv" ]
CMD [ "run", "python", "plotr_signal/main.py" ]
