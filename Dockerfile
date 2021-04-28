FROM python:3.8-alpine

RUN apk add --no-cache postgresql-libs && \
    apk add --no-cache --virtual .build-deps build-base gcc musl-dev postgresql-dev && \
    pip install --upgrade pip &&\
    pip install pipenv

COPY ./ /app/

WORKDIR /app

RUN pipenv install -e .

RUN apk add --no-cache libstdc++ && \
    apk --purge del .build-deps

EXPOSE 5000

ENTRYPOINT [ "pipenv" ]
CMD [ "run", "python", "plotr_signal/main.py" ]
