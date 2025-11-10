FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json ./
COPY tsconfig.json ./
COPY src ./src

RUN npm install && npm run build

EXPOSE 8003

CMD ["node", "dist/index.js"]
