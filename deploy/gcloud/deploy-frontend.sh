#!/usr/bin/env bash
# shellcheck source=deploy/gcloud/common.sh
source "$(dirname "$0")/common.sh"
require_cloud
command -v firebase >/dev/null || { echo 'Install firebase-tools and run firebase login first.' >&2; exit 1; }
API_URL="$(api_url)"
[[ "$API_URL" == https://* ]] || { echo 'Deploy the API first.' >&2; exit 1; }
cd "$ROOT/miniapp"
npm ci
VITE_API_URL="$API_URL/api/v1" VITE_DEV_AUTH=false npm run build
# Initialize Firebase on this GCP project once using: firebase projects:addfirebase PROJECT_ID
firebase deploy --only hosting --project="$PROJECT_ID" --non-interactive
printf 'Frontend deployed. Open %s from Telegram.\n' "$FRONTEND_URL"
