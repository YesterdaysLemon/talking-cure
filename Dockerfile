FROM node:22-alpine AS build
RUN apk add --no-cache git
WORKDIR /app
COPY package.json server.mjs ./
COPY scripts ./scripts
COPY public ./public
COPY content ./content
COPY .git ./.git
RUN npm run build && npm run check && git rev-parse HEAD > build-sha.txt
FROM node:22-alpine
WORKDIR /app
COPY --from=build /app/dist ./dist
COPY --from=build /app/server.mjs /app/build-sha.txt ./
ENV PORT=8080
USER node
EXPOSE 8080
CMD ["node", "server.mjs"]
