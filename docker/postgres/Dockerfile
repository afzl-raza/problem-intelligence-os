# PostgreSQL 16 plus the pgvector extension, built on the same base image the
# existing data volume was created on (keeps the OS and glibc, and therefore
# text-index collation, unchanged -- unlike swapping to pgvector/pgvector,
# which is built on an older Debian).
FROM postgres:16

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-16-pgvector \
    && rm -rf /var/lib/apt/lists/*
