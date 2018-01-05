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


EXPOSE 5000

CMD ["passport", "server", "run", "--host=0.0.0.0", "--consul"]
