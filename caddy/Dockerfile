# Multi-stage build of Caddy with the DuckDNS DNS provider plugin.
# Needed so Caddy can solve the ACME DNS-01 challenge by creating a TXT
# record at DuckDNS — proving we control the domain without exposing
# port 80 to the public internet.

FROM caddy:2-builder AS builder
RUN xcaddy build \
    --with github.com/caddy-dns/duckdns

FROM caddy:2-alpine
COPY --from=builder /usr/bin/caddy /usr/bin/caddy
