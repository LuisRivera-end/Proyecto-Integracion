#!/bin/sh

# Bucle simple para esperar que la DB esté lista
while ! nc -z mariadb 3306; do
    echo "Esperando que MariaDB se inicie..."
    sleep 1
done

echo "MariaDB está lista. Iniciando la aplicación..."

# El comando inicia la app Flask
exec "$@"