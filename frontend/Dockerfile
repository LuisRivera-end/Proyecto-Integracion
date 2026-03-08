# Etapa de build y ejecución para Nuxt 3
FROM node:20-alpine
WORKDIR /app
COPY nuxt/package*.json ./
RUN npm install
COPY nuxt/ ./
RUN npm run build
EXPOSE 3000
CMD ["node", ".output/server/index.mjs"]