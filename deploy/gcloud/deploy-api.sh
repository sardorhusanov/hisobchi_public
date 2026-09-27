#!/usr/bin/env bash
# shellcheck source=deploy/gcloud/common.sh
source "$(dirname "$0")/common.sh"
require_cloud
INSTANCE_CONNECTION_NAME="$(connection_name)"
if [[ -n "${DEPLOY_IMAGE:-}" ]]; then
  API_IMAGE=$DEPLOY_IMAGE
else
  TAG="$(date -u +%Y%m%d%H%M%S)-$(git -C "$ROOT" rev-parse --short HEAD)"
  API_IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/$AR_REPO/api:$TAG"
  gc builds submit "$ROOT/backend" --config="$ROOT/backend/cloudbuild.yaml" \
    --service-account="projects/$PROJECT_ID/serviceAccounts/$BUILD_SERVICE_ACCOUNT" \
    --substitutions="_IMAGE=$API_IMAGE"
fi
# Pin the actual image, and enabled secret versions, for this release.
DIGEST="$(gc artifacts docker images describe "$API_IMAGE" --format='value(image_summary.digest)')"
[[ "$DIGEST" == sha256:* ]] || { echo 'Could not resolve image digest.' >&2; exit 1; }
IMAGE="$REGION-docker.pkg.dev/$PROJECT_ID/$AR_REPO/api@$DIGEST"
DB_VERSION="$(secret_version hisobchi-api-database-url)"
TOKEN_VERSION="$(secret_version hisobchi-bot-token)"
[[ -n "$DB_VERSION" && -n "$TOKEN_VERSION" ]] || { echo 'Run provision.sh first.' >&2; exit 1; }
SECRETS="DATABASE_URL=hisobchi-api-database-url:${DB_VERSION##*/},BOT_TOKEN=hisobchi-bot-token:${TOKEN_VERSION##*/}"
ENV_VARS="APP_ENV=production,TIMEZONE=Asia/Tashkent,CORS_ORIGINS=$FRONTEND_URL,MINI_APP_URL=$FRONTEND_URL,DEV_TELEGRAM_USER_ID="

# A failed migration stops deployment; no API traffic reaches the new revision.
gc run jobs deploy "$RUN_SERVICE-migrate" --image="$IMAGE" --region="$REGION" \
  --service-account="$SERVICE_ACCOUNT" --set-cloudsql-instances="$INSTANCE_CONNECTION_NAME" \
  --set-secrets="$SECRETS" --set-env-vars="$ENV_VARS" \
  --command=alembic --args=upgrade,head --tasks=1 --parallelism=1 \
  --max-retries=0 --task-timeout=300s --memory=512Mi --cpu=1
gc run jobs execute "$RUN_SERVICE-migrate" --region="$REGION" --wait

gc run deploy "$RUN_SERVICE" --image="$IMAGE" --region="$REGION" \
  --platform=managed --execution-environment=gen2 --allow-unauthenticated \
  --service-account="$SERVICE_ACCOUNT" --set-cloudsql-instances="$INSTANCE_CONNECTION_NAME" \
  --set-secrets="$SECRETS" --set-env-vars="$ENV_VARS" \
  --memory=512Mi --cpu=1 --min-instances=0 --max-instances=2 --concurrency=40 --timeout=60
API_URL="$(api_url)"
curl --fail --silent --show-error --retry 5 --retry-all-errors "$API_URL/health"
printf '\nAPI deployed: %s\n' "$API_URL"
