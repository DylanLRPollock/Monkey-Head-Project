# syntax=docker/dockerfile:1.7

ARG DEBIAN_VERSION=trixie
ARG DEBIAN_VARIANT=slim
ARG PYTHON_VERSION=3.13.5
ARG APP_USER=app
ARG APP_UID=1000
ARG APP_GID=1000
ARG TZ=Etc/UTC
ARG LANG=en_US.UTF-8
ARG LC_ALL=en_US.UTF-8

# -------- Stage: build CPython --------
FROM debian:${DEBIAN_VERSION}-${DEBIAN_VARIANT} AS cpython
ARG PYTHON_VERSION
ENV DEBIAN_FRONTEND=noninteractive
RUN --mount=type=cache,target=/var/cache/apt,id=apt-cpython,sharing=locked     set -eux;     apt-get update;     apt-get install -y --no-install-recommends       build-essential ca-certificates curl wget xz-utils       libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev       libffi-dev liblzma-dev tk-dev uuid-dev;     rm -rf /var/lib/apt/lists*
WORKDIR /tmp/src
RUN set -eux;     curl -fsSLo Python-${PYTHON_VERSION}.tgz https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz;     tar -xzf Python-${PYTHON_VERSION}.tgz
WORKDIR /tmp/src/Python-${PYTHON_VERSION}
RUN --mount=type=cache,target=/tmp/build-cache,id=py-build,sharing=locked     set -eux;     ./configure --prefix=/usr/local --enable-optimizations --with-lto --enable-shared;     make -j"$(nproc)";     make install;     ldconfig;     python3 -V; pip3 --version

# -------- Stage: runtime --------
FROM debian:${DEBIAN_VERSION}-${DEBIAN_VARIANT} AS runtime
ARG APP_USER APP_UID APP_GID TZ LANG LC_ALL
ENV DEBIAN_FRONTEND=noninteractive     PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1     PIP_DISABLE_PIP_VERSION_CHECK=1     TZ=${TZ} LANG=${LANG} LC_ALL=${LC_ALL}

RUN --mount=type=cache,target=/var/cache/apt,id=apt-runtime,sharing=locked     set -eux;     apt-get update;     apt-get install -y --no-install-recommends       ca-certificates curl git bash tini locales tzdata procps       iproute2 iputils-ping dnsutils nano less;     echo "${TZ}" > /etc/timezone;     ln -snf "/usr/share/zoneinfo/${TZ}" /etc/localtime;     dpkg-reconfigure -f noninteractive tzdata;     sed -i "s/^# ${LANG} UTF-8/${LANG} UTF-8/" /etc/locale.gen || true;     locale-gen;     rm -rf /var/lib/apt/lists/*

# Bring in CPython and register the shared library path
COPY --from=cpython /usr/local /usr/local
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
RUN echo "/usr/local/lib" > /etc/ld.so.conf.d/usr-local.conf && ldconfig

# Non-root user
RUN set -eux; groupadd -g "${APP_GID}" "${APP_USER}"; useradd -m -u "${APP_UID}" -g "${APP_GID}" -s /bin/bash "${APP_USER}"

# Virtualenv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="${VIRTUAL_ENV}/bin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
RUN python3 -m venv "${VIRTUAL_ENV}" && "${VIRTUAL_ENV}/bin/pip" install --no-cache-dir -U pip setuptools wheel

WORKDIR /workspace

# Optional requirements without failing when file absent
RUN --mount=type=bind,source=.,target=/src     --mount=type=cache,target=/root/.cache/pip,id=pip-cache,sharing=locked     bash -lc 'if [ -f /src/requirements.txt ]; then pip install -r /src/requirements.txt; fi'

USER ${APP_USER}
EXPOSE 1995

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=5   CMD python -c "import sys; sys.exit(0)"

LABEL org.opencontainers.image.title="Monkey Head Project Dev Image"       org.opencontainers.image.description="Debian ${DEBIAN_VERSION} + CPython ${PYTHON_VERSION} dev toolbox (non-root, venv, tini)"       org.opencontainers.image.licenses="MIT"

ENTRYPOINT ["/usr/bin/tini","--"]
CMD ["sleep","infinity"]

# Compose target
FROM runtime AS dev
