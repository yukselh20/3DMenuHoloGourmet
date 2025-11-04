# Use Node.js for development
FROM node:24-slim

# Set working directory
WORKDIR /app/frontend

# Copy package files first (for better caching)
COPY package.json yarn.lock ./

# Install dependencies
RUN yarn install --frozen-lockfile

# Copy all source code
COPY . .

# Expose port 3000 for React development server
EXPOSE 3000

# Start the development server with hot reload
CMD ["yarn", "start"]