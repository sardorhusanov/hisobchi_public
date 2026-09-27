#!/usr/bin/env bash
# shellcheck source=deploy/gcloud/common.sh
source "$(dirname "$0")/common.sh"
require_cloud
API_URL="$(api_url)"
curl --fail --silent --show-error "$API_URL/health"
printf '\n'
status="$(curl --silent --show-error -o /dev/null -w '%{http_code}' "$API_URL/api/v1/me")"
[[ "$status" == 401 ]] || { echo "Expected protected API to return 401, got $status" >&2; exit 1; }
headers="$(curl --fail --silent --show-error -D - -o /dev/null -X OPTIONS "$API_URL/api/v1/me" \
  -H "Origin: $FRONTEND_URL" -H 'Access-Control-Request-Method: GET' \
  -H 'Access-Control-Request-Headers: authorization')"
grep -Fiq "access-control-allow-origin: $FRONTEND_URL" <<< "$headers"
curl --fail --silent --show-error "$FRONTEND_URL" -o /dev/null
curl --fail --silent --show-error "$FRONTEND_URL/projects" -o /dev/null
gc compute ssh "$VM_NAME" --zone="$ZONE" \
  --command='sudo systemctl is-active cloud-sql-proxy hisobchi-bot'
echo 'HTTP, authentication boundary, CORS, SPA route, and VM service checks passed.'
echo 'Finish in Telegram: /start, open Mini App, save a record, reopen, and check shared bot data.'
