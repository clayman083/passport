FROM python:3.7.0b5-alpine3.7

ARG app_version

# Copy application distribution package
COPY dist/passport-${app_version}.tar.gz /root/

# Install required packages
RUN apk add --update --no-cache make libc-dev python3-dev linux-headers gcc g++ postgresql-client && \
    pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir /root/passport-${app_version}.tar.gz && \
    rm /root/passport-${app_version}.tar.gz && \
    apk del make libc-dev python3-dev linux-headers gcc g++

RUN mkdir -p /usr/share/passport && cp /usr/local/lib/python3.7/site-packages/passport/storage/sql/* /usr/share/passport

EXPOSE 5000

CMD ["passport", "server", "run", "--host=0.0.0.0", "--consul"]
