#!/usr/bin/env bash
# Create infrastructure once; reruns reuse credentials and existing resources.
# shellcheck source=deploy/gcloud/common.sh
source "$(dirname "$0")/common.sh"
require_cloud
gc services enable compute.googleapis.com run.googleapis.com sqladmin.googleapis.com \
  artifactregistry.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com \
  iam.googleapis.com firebase.googleapis.com firebasehosting.googleapis.com

gc iam service-accounts describe "$SERVICE_ACCOUNT" >/dev/null 2>&1 || \
  gc iam service-accounts create "$SERVICE_ACCOUNT_NAME" --display-name='Hisobchi runtime'
gc projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$SERVICE_ACCOUNT" --role=roles/cloudsql.client --condition=None >/dev/null
gc iam service-accounts describe "$BUILD_SERVICE_ACCOUNT" >/dev/null 2>&1 || \
  gc iam service-accounts create hisobchi-build --display-name='Hisobchi image builds'
gc projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:$BUILD_SERVICE_ACCOUNT" --role=roles/cloudbuild.builds.builder --condition=None >/dev/null

gc sql instances describe "$DB_INSTANCE" >/dev/null 2>&1 || \
  gc sql instances create "$DB_INSTANCE" --database-version=POSTGRES_15 \
    --edition=ENTERPRISE --tier=db-f1-micro --region="$REGION" \
    --storage-type=SSD --storage-size=10GB --storage-auto-increase \
    --availability-type=ZONAL --backup-start-time=18:00 --retained-backups-count=7
gc sql databases describe "$DB_NAME" --instance="$DB_INSTANCE" >/dev/null 2>&1 || \
  gc sql databases create "$DB_NAME" --instance="$DB_INSTANCE"

# The saved password makes interrupted first-time provisioning resumable.
ensure_secret() {
  local name=$1
  gc secrets describe "$name" >/dev/null 2>&1 || \
    gc secrets create "$name" --replication-policy=automatic >/dev/null
}
ensure_secret hisobchi-db-password
if [[ -z "$(secret_version hisobchi-db-password)" ]]; then
  openssl rand -hex 24 | tr -d '\n' | gc secrets versions add hisobchi-db-password --data-file=- >/dev/null
fi
DB_PASSWORD="$(gc secrets versions access latest --secret=hisobchi-db-password)"
[[ "$DB_PASSWORD" =~ ^[a-f0-9]{48}$ ]] || { echo 'Unexpected saved database password format; investigate before continuing.' >&2; exit 1; }
users="$(gc sql users list --instance="$DB_INSTANCE" --format='value(name)')"
if ! grep -Fxq "$DB_USER" <<< "$users"; then
  gc sql users create "$DB_USER" --instance="$DB_INSTANCE" --password="$DB_PASSWORD"
fi

INSTANCE_CONNECTION_NAME="$(connection_name)"
for name in hisobchi-api-database-url hisobchi-bot-database-url; do
  ensure_secret "$name"
  if [[ -z "$(secret_version "$name")" ]]; then
    if [[ "$name" == hisobchi-api-database-url ]]; then
      url="postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@/${DB_NAME}?host=/cloudsql/${INSTANCE_CONNECTION_NAME}"
    else
      url="postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@127.0.0.1:5432/${DB_NAME}"
    fi
    printf '%s' "$url" | gc secrets versions add "$name" --data-file=- >/dev/null
  fi
done
unset DB_PASSWORD url

ensure_secret hisobchi-bot-token
if [[ -z "$(secret_version hisobchi-bot-token)" ]]; then
  if [[ -z "${BOT_TOKEN:-}" ]]; then
    read -r -s -p 'Telegram bot token: ' BOT_TOKEN
    printf '\n'
  fi
  [[ "$BOT_TOKEN" =~ ^[0-9]+:[A-Za-z0-9_-]+$ ]] || { echo 'Invalid Telegram token format.' >&2; exit 1; }
  printf '%s' "$BOT_TOKEN" | gc secrets versions add hisobchi-bot-token --data-file=- >/dev/null
fi
unset BOT_TOKEN
for name in hisobchi-bot-token hisobchi-api-database-url hisobchi-bot-database-url; do
  gc secrets add-iam-policy-binding "$name" --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role=roles/secretmanager.secretAccessor --condition=None >/dev/null
done

gc artifacts repositories describe "$AR_REPO" --location="$REGION" >/dev/null 2>&1 || \
  gc artifacts repositories create "$AR_REPO" --repository-format=docker --location="$REGION" \
    --description='Hisobchi application images'
echo "Infrastructure prepared in $PROJECT_ID. Next: bash deploy/gcloud/deploy-api.sh"
