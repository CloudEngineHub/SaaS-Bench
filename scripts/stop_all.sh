#!/usr/bin/env bash
# Stop and remove all rollout_* containers and their anonymous volumes
# A custom prefix may be set via SAAS_SLOT_PREFIX (default: rollout)
PREFIX="${SAAS_SLOT_PREFIX:-rollout}"
docker ps -a --format "{{.Names}}" | grep "^${PREFIX}_" | xargs -r docker stop
docker ps -a --format "{{.Names}}" | grep "^${PREFIX}_" | xargs -r docker rm -v
# Remove all rollout_* named volumes (created by compose-based apps)
docker volume ls --format "{{.Name}}" | grep "^${PREFIX}_" | xargs -r docker volume rm
