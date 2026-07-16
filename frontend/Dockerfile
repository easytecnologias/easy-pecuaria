# build do Vue
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
# API na mesma origem, via proxy do nginx
ENV VITE_API_URL=/api
RUN npm run build

# serve estatico + proxy /api
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
