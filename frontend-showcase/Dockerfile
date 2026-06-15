FROM node:20-alpine AS build

WORKDIR /app

ARG VITE_MISSION_CONTROL_STATUS_URL=https://workflow-legion-production.up.railway.app/mission-control-status
ENV VITE_MISSION_CONTROL_STATUS_URL=$VITE_MISSION_CONTROL_STATUS_URL

COPY frontend-showcase/package*.json ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

COPY frontend-showcase/ ./
RUN npm run build

FROM node:20-alpine AS runtime

WORKDIR /app

ENV NODE_ENV=production

RUN npm install -g serve

COPY --from=build /app/dist ./dist

CMD ["sh", "-c", "serve -s dist -l ${PORT:-3000}"]
