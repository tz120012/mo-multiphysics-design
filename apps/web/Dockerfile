# Mo Web — Vue build + nginx (build from repo root so wasm pkg is visible)
#   docker build -f apps/web/Dockerfile .
# Compose: web.build.context=.  dockerfile: apps/web/Dockerfile
FROM node:20-alpine AS build
WORKDIR /src/apps/web
RUN corepack enable && corepack prepare pnpm@10.34.6 --activate
COPY apps/web/package.json apps/web/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY apps/web/ ./
# vite.config aliases @mo/solver-analytic-wasm → <repo>/packages/solver-analytic-wasm/pkg
COPY packages/solver-analytic-wasm /src/packages/solver-analytic-wasm
ENV VITE_API_BASE=/api/v1
RUN pnpm build

FROM nginx:1.27-alpine
COPY --from=build /src/apps/web/dist /usr/share/nginx/html
COPY apps/web/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
HEALTHCHECK --interval=5s --timeout=3s --retries=10 \
  CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1
