FROM python:3.8-alpine3.11 as build

RUN apk add --update --no-cache --quiet make libc-dev libffi-dev python3-dev linux-headers gcc g++ git postgresql-dev && \
    python3 -m pip install --no-cache-dir --quiet -U pip && \
    python3 -m pip install --no-cache-dir --quiet poetry

ADD . /app

WORKDIR /app

RUN poetry build


FROM python:3.8-alpine3.11

COPY --from=build /app/dist/*.whl .

RUN apk add --update --no-cache --quiet make openssl-dev libc-dev libffi-dev python3-dev linux-headers gcc g++ git postgresql-client && \
    python3 -m pip install --no-cache-dir --quiet -U pip && \
    python3 -m pip install --no-cache-dir --quiet *.whl && \
    mkdir -p /usr/share/passport && \
    rm -f *.whl && \
    apk del --quiet make libc-dev libffi-dev python3-dev linux-headers gcc g++ git

ADD ./src/passport/storage/sql /usr/share/passport

EXPOSE 5000

ENTRYPOINT ["python3", "-m", "passport"]

CMD ["--conf-dir", "/etc/passport", "server", "run"]
