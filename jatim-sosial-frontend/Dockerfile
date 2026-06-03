# Stage 1: Base image with dependencies installed
FROM node:20-alpine AS base
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .

# Stage 2: Development mode (Vite Dev Server with Hot-Reload)
FROM base AS dev
EXPOSE 5173
CMD ["npm", "run", "dev"]

# Stage 3: Production compilation
FROM base AS build
RUN npm run build

# Stage 4: Production Nginx Server
FROM nginx:stable-alpine AS prod
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
