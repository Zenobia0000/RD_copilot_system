# Stage 1: Build
FROM node:22-alpine AS build

WORKDIR /app

# Copy dependency files first for layer caching
COPY package.json package-lock.json ./

RUN npm ci

# Copy source files
COPY index.html vite.config.ts tsconfig*.json tailwind.config.ts postcss.config.js components.json ./
COPY src/ src/
COPY public/ public/

# Build args for Vite env vars (baked into static files at build time)
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_PUBLISHABLE_KEY
ARG VITE_SUPABASE_SERVICE_ROLE_KEY
ARG VITE_API_BASE_URL

RUN npm run build

# Stage 2: Serve
FROM nginx:alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built files from build stage
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
