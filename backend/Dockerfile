FROM python:3.12-alpine
WORKDIR /app
RUN apk add --no-cache \
    cups \
    cups-client \
    cups-libs \
    ghostscript \
    poppler-utils \
    netcat-openbsd \
    jpeg-dev \
    zlib-dev \
    gcc \
    musl-dev \
    python3-dev
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN apk add --no-cache netcat-openbsd
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
EXPOSE 5000
CMD ["python", "run.py"]