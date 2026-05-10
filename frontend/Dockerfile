FROM node:18-alpine

WORKDIR /app

COPY package.json package-lock.json* yarn.lock* ./

RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev"]
