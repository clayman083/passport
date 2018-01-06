FROM python:alpine

ARG app_version

# Install required packages
RUN apk add --update --no-cache make libc-dev python3-dev linux-headers gcc postgresql-client

# Copy application distribution package
COPY dist/passport-${app_version}.tar.gz /root/

# Install application package
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir /root/passport-${app_version}.tar.gz && \
    rm /root/passport-${app_version}.tar.gz

RUN mkdir -p /usr/share/passport && cp /usr/local/lib/python3.6/site-packages/passport/storage/sql/* /usr/share/passport

EXPOSE 5000

CMD ["passport", "server", "run", "--host=0.0.0.0", "--consul"]
