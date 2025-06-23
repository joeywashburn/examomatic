FROM node:20 AS build
WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm install -g @angular/cli && npm install --legacy-peer-deps

# Copy source code
COPY . .

# Build the application
RUN ng build --configuration production --aot

# Production stage
FROM nginx:alpine

# Remove default nginx files
RUN rm -rf /usr/share/nginx/html/*

# Copy the built application
# Note: Copy contents of the build directory, not the directory itself
COPY --from=build /app/dist/exam-o-matic/browser /usr/share/nginx/html/

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create nginx user and set permissions
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]