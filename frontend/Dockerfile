FROM node:18-alpine

WORKDIR /usr/src/app

# Install dependencies first (better caching)
COPY package*.json ./
RUN npm config set fetch-timeout 300000 && \
    npm config set registry https://registry.npmjs.org/ && \
    npm install

# Copy the rest of the application
COPY ./ .

EXPOSE 3000

# Set the host for development
CMD ["npm", "run", "start", "--", "--host"]