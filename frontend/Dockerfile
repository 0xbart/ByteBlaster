# Frontend-only build. No backend coupling.
#
# Requires `src/api/schema.d.ts` to be present (checked into the image build
# context). Regenerate before building when the backend OpenAPI schema changes:
#
#   ./scripts/generate-client.sh           # needs the backend running locally
#   docker compose build frontend
#
# Build context: ./frontend  (set in docker-compose.yml).

# --- Stage 1: install deps + build Vue app ---
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . ./
# Fail early with a clear message if the generated client is missing.
RUN test -s src/api/schema.d.ts || (echo "ERROR: src/api/schema.d.ts missing. Run ./scripts/generate-client.sh before building." && exit 1)
RUN npm run build

# --- Stage 2: serve static assets behind nginx with /api + /ws proxy ---
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
