FROM node:20-alpine

WORKDIR /app

COPY package.json /app/package.json
RUN npm install

COPY index.html /app/index.html
COPY vite.config.ts /app/vite.config.ts
COPY tsconfig.json /app/tsconfig.json
COPY src /app/src

EXPOSE 3000
CMD ["npm", "run", "dev"]


