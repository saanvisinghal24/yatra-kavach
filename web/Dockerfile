FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
ARG VITE_PUBLIC_ORIGIN
ARG VITE_CONTACT_EMAIL
ENV VITE_PUBLIC_ORIGIN=$VITE_PUBLIC_ORIGIN VITE_CONTACT_EMAIL=$VITE_CONTACT_EMAIL
RUN npm run build
FROM caddy:2-alpine
COPY --from=build /app/dist /srv
COPY Caddyfile /etc/caddy/Caddyfile

COPY Caddyfile.render /etc/caddy/Caddyfile.render
