FROM node:22-alpine

WORKDIR /app/frontend

COPY frontend/package*.json ./

RUN npm install

CMD ["npm", "run", "dev", "--", "--hostname", "0.0.0.0", "--port", "3000"]
