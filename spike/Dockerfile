# Minimal static server for Gears (spike, not production-hardened).
# Build from repo root:  docker build -f spike/Dockerfile -t gears .
# Run:                   docker run --rm -p 8080:80 gears
# Behind an edge Caddy:  reverse_proxy gears:80 (TLS terminates at the edge).
FROM caddy:2-alpine
COPY spike/Caddyfile /etc/caddy/Caddyfile
COPY public/ /srv/
EXPOSE 80
