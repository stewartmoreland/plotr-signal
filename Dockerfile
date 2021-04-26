FROM python:3.8-slim-buster

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    gcc && \
    pip install --upgrade pip \
    pip install pipenv

COPY ./ /app/

WORKDIR /app

RUN pipenv install -e .

EXPOSE 5000

ENTRYPOINT [ "pipenv" ]
CMD [ "run", "python", "plotr_signal/main.py" ]
