#!/usr/bin/env bash
# Shared configuration is consumed by scripts that source this file.
# shellcheck disable=SC2034
set -euo pipefail
# Never trace commands: some operations handle credentials.
set +x
DEPLOY_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$DEPLOY_DIR/../.." && pwd)"
if [[ -f "$DEPLOY_DIR/config.env" ]]; then
  # shellcheck source=/dev/null
  source "$DEPLOY_DIR/config.env"
fi
if ! command -v gcloud >/dev/null && [[ -x "$HOME/google-cloud-sdk/bin/gcloud" ]]; then
  export PATH="$HOME/google-cloud-sdk/bin:$PATH"
fi
: "${PROJECT_ID:?Set PROJECT_ID in deploy/gcloud/config.env or your environment}"
[[ "$PROJECT_ID" =~ ^[a-z][a-z0-9-]{4,28}[a-z0-9]$ ]] || { echo 'Invalid project ID' >&2; exit 1; }
REGION=${REGION:-asia-south2}
ZONE=${ZONE:-asia-south2-a}
DB_INSTANCE=${DB_INSTANCE:-hisobchi-db}
DB_NAME=${DB_NAME:-hisobchi}
DB_USER=${DB_USER:-hisobchi_app}
VM_NAME=${VM_NAME:-hisobchi-bot}
RUN_SERVICE=${RUN_SERVICE:-hisobchi-api}
AR_REPO=${AR_REPO:-hisobchi}
SERVICE_ACCOUNT_NAME=${SERVICE_ACCOUNT_NAME:-hisobchi-runtime}
SERVICE_ACCOUNT="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"
BUILD_SERVICE_ACCOUNT="hisobchi-build@$PROJECT_ID.iam.gserviceaccount.com"
FRONTEND_URL=${FRONTEND_URL:-https://$PROJECT_ID.web.app}
NETWORK=${NETWORK:-default}
SUBNET=${SUBNET:-default}
PROXY_VERSION=${PROXY_VERSION:-2.25.4}
for value in "$REGION" "$ZONE" "$DB_INSTANCE" "$VM_NAME" "$RUN_SERVICE" "$AR_REPO" "$SERVICE_ACCOUNT_NAME" "$NETWORK" "$SUBNET"; do
  [[ "$value" =~ ^[a-z][a-z0-9-]*$ ]] || { echo 'Invalid resource name' >&2; exit 1; }
done
for value in "$DB_NAME" "$DB_USER"; do
  [[ "$value" =~ ^[a-z][a-z0-9_]*$ ]] || { echo 'Invalid database name/user' >&2; exit 1; }
done
[[ "$FRONTEND_URL" =~ ^https://[a-zA-Z0-9.-]+$ ]] || { echo 'FRONTEND_URL must be an HTTPS origin without a trailing slash' >&2; exit 1; }
[[ "$PROXY_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || exit 1
gc() { gcloud --project="$PROJECT_ID" "$@"; }
require_cloud() {
  command -v gcloud >/dev/null || { echo 'Install Google Cloud CLI first.' >&2; exit 1; }
  [[ -n "$(gc auth list --filter=status:ACTIVE --format='value(account)')" ]] || { echo 'Run gcloud auth login first.' >&2; exit 1; }
  [[ "$(gc billing projects describe "$PROJECT_ID" --format='value(billingEnabled)')" == True ]] || { echo 'Enable billing on the selected project first.' >&2; exit 1; }
}
connection_name() { gc sql instances describe "$DB_INSTANCE" --format='value(connectionName)'; }
api_url() { gc run services describe "$RUN_SERVICE" --region="$REGION" --format='value(status.url)'; }
secret_version() {
  gc secrets versions list "$1" --filter=state:ENABLED --sort-by='~createTime' --limit=1 --format='value(name)'
}
