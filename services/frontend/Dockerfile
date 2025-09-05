FROM node:20-alpine

WORKDIR /app

# Only copy package files and install dependencies
COPY package.json package-lock.json ./
RUN npm install

# Don't copy source code - let volume mount handle it
# Don't build - dev server will handle it

EXPOSE 3000

CMD ["npm", "run", "dev"]