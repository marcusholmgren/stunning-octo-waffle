# Use an official Node.js runtime as a parent image
FROM node:22-alpine AS builder

# Set the working directory in the container
WORKDIR /app

# Copy package.json and package-lock.json (if available)
COPY package*.json ./

# Install app dependencies
RUN npm install # --production # Use --production for smaller image size

# Copy the rest of your application's code
COPY . .

# Define build arguments (with optional default values)
ARG VITE_KEYCLOAK_URL
ARG VITE_KEYCLOAK_REALM
ARG VITE_KEYCLOAK_CLIENT_ID
ARG VITE_KEYCLOAK_REDIRECT_URI
ARG VITE_BACKEND_URL

# Set environment variables for the build process, using the build arguments
ENV VITE_KEYCLOAK_URL=$VITE_KEYCLOAK_URL
ENV VITE_KEYCLOAK_REALM=$VITE_KEYCLOAK_REALM
ENV VITE_KEYCLOAK_CLIENT_ID=$VITE_KEYCLOAK_CLIENT_ID
ENV VITE_KEYCLOAK_REDIRECT_URI=$VITE_KEYCLOAK_REDIRECT_URI
ENV VITE_BACKEND_URL=$VITE_BACKEND_URL

# Build the React app
RUN npm run build

#---

# Use a lightweight server like nginx to serve the static files
FROM nginx:alpine

# Copy the build output from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port (nginx default is 80)
EXPOSE 80

# Start nginx when the container starts
CMD ["nginx", "-g", "daemon off;"]