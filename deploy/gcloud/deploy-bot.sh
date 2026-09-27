#!/usr/bin/env bash
# shellcheck source=deploy/gcloud/common.sh
source "$(dirname "$0")/common.sh"
require_cloud
INSTANCE_CONNECTION_NAME="$(connection_name)"
gc compute instances describe "$VM_NAME" --zone="$ZONE" >/dev/null 2>&1 || \
  gc compute instances create "$VM_NAME" --zone="$ZONE" --machine-type=e2-small \
    --image-family=ubuntu-2404-lts-amd64 --image-project=ubuntu-os-cloud \
    --boot-disk-size=10GB --boot-disk-type=pd-balanced \
    --network="$NETWORK" --subnet="$SUBNET" \
    --service-account="$SERVICE_ACCOUNT" --scopes=cloud-platform

stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT
# Explicit allowlist: no .env, local interpreter, test artifacts, or credentials.
tar -C "$ROOT/backend" --exclude='__pycache__' --exclude='*.pyc' --exclude='.env*' \
  -czf "$stage/backend.tar.gz" app alembic alembic.ini pyproject.toml uv.lock
cp "$DEPLOY_DIR/setup-vm.sh" "$stage/setup-vm.sh"
printf 'PROJECT_ID=%s\nINSTANCE_CONNECTION_NAME=%s\nFRONTEND_URL=%s\nPROXY_VERSION=%s\n' \
  "$PROJECT_ID" "$INSTANCE_CONNECTION_NAME" "$FRONTEND_URL" "$PROXY_VERSION" > "$stage/vm.env"
remote_stage="$(gc compute ssh "$VM_NAME" --zone="$ZONE" --command='mktemp -d /tmp/hisobchi-deploy.XXXXXXXX')"
[[ "$remote_stage" =~ ^/tmp/hisobchi-deploy\.[A-Za-z0-9]+$ ]] || { echo 'Unexpected remote staging path.' >&2; exit 1; }
gc compute scp "$stage/backend.tar.gz" "$stage/setup-vm.sh" "$stage/vm.env" \
  "$VM_NAME:$remote_stage/" --zone="$ZONE"
gc compute ssh "$VM_NAME" --zone="$ZONE" \
  --command="sudo bash '$remote_stage/setup-vm.sh' '$remote_stage'"
echo 'Bot installed. Test /start in Telegram; keep all other polling processes stopped.'
