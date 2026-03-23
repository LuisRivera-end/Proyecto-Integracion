# Etapa de build y ejecución para Nuxt 3
FROM node:20-alpine
WORKDIR /app
COPY nuxt/package*.json ./
RUN npm install
COPY nuxt/ ./
RUN npm run build

# Asignar la propiedad al usuario 'node' que ya viene con la imagen
RUN chown -R node:node /app

# Ejecutar como usuario 'node' sin privilegios de root
USER node

EXPOSE 3000
CMD ["node", ".output/server/index.mjs"]