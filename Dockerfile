FROM python:3.10-slim-bullseye

RUN apt update && apt upgrade -y && \
    apt install -y postgresql-client && \
    apt install -y \
        gcc \
        musl-dev \
        librdkafka-dev && \
    pip install --upgrade pip

# RUN pip install --upgrade pandas==1.4.2 --no-cache-dir

COPY ./ /app/

WORKDIR /app

RUN pip install -e .

EXPOSE 5000

ENTRYPOINT [ "python" ]
CMD [ "src/plotr_signal/main.py" ]
