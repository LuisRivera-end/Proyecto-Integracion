FROM python:3.12-alpine
WORKDIR /app

# Crear usuario sin privilegios
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

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
    python3-dev \
    espeak
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN apk add --no-cache netcat-openbsd
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh \
    && chown -R appuser:appgroup /app \
    && chown appuser:appgroup /usr/local/bin/entrypoint.sh

# Cambiar a usuario sin privilegios
USER appuser

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
EXPOSE 5000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000"]