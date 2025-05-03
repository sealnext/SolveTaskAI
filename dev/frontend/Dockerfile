FROM node:23-bookworm-slim AS base

ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"

RUN apt-get update && apt-get install -y curl
RUN curl -fsSL https://get.pnpm.io/install.sh | /bin/bash -

RUN groupadd -r app_group && useradd -r -g app_group app_user
COPY --chown=app_user:app_group . /app
WORKDIR /app

FROM base AS prod-deps
RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --prod --frozen-lockfile

FROM base AS build
RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --frozen-lockfile
RUN pnpm run build

FROM base
COPY --from=build --chown=app_user:app_group /app/build /app/build
COPY --from=prod-deps --chown=app_user:app_group /app/node_modules /app/node_modules
USER app_user

CMD [ "pnpm", "start", "--host", "--port", "5173" ]
EXPOSE 5173
