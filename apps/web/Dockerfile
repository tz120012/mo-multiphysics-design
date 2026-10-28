# Mo Web — Vue build + nginx (dev-compose one-click)
FROM node:20-alpine AS build
WORKDIR /web
RUN corepack enable && corepack prepare pnpm@10.34.6 --activate
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
# Browser calls same-origin /api/v1 → nginx proxies to api:8000
ENV VITE_API_BASE=/api/v1
RUN pnpm build

FROM nginx:1.27-alpine
COPY --from=build /web/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
HEALTHCHECK --interval=5s --timeout=3s --retries=10 \
  CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1
