# Hisobchi on Google Cloud

This deployment follows the supplied architecture: one polling bot on Compute
Engine, FastAPI on Cloud Run, PostgreSQL on Cloud SQL, and the React Mini App on
Firebase Hosting. Both the bot and API connect directly to the same database.
The bot does not call FastAPI. No reverse proxy or custom domain is needed.

| Resource | Configuration |
| --- | --- |
| Region / VM zone | `asia-south2` / `asia-south2-a` |
| Bot VM | `hisobchi-bot`, `e2-small`, Ubuntu 24.04, 10 GB disk |
| API | `hisobchi-api`, 1 CPU, 512 MiB, 0–2 instances, concurrency 40 |
| Database | `hisobchi-db`, PostgreSQL 15 Enterprise, `db-f1-micro`, single zone |
| Database storage | 10 GB SSD, automatic growth, seven daily backups |
| Frontend | Default Firebase site, `https://PROJECT_ID.web.app` |

The VM and database continue to incur charges when the API scales to zero.
This creates an empty production database; local development records are not copied.

## First deployment

Install Google Cloud CLI, Firebase CLI (`npm install -g firebase-tools`), Node
22.12+ (24+ for tests), Python 3.13, and uv. Use a Google account permitted to
enable services, create resources and service accounts, grant IAM roles, and
deploy Cloud Run/Firebase. The scripts use an explicit project for every cloud
command, without changing your global gcloud project setting.

```bash
gcloud auth login
firebase login
cp deploy/gcloud/config.env.example deploy/gcloud/config.env
```

Set `PROJECT_ID` in `config.env` to your existing, billing-enabled project.
For this deployment it is `hisobchi-509915`; the local ignored config is already
prepared. Do not overwrite it with the example if it already exists.
The scripts also find `~/google-cloud-sdk/bin/gcloud` if it is not on PATH.

From the repository root, run in this order:

```bash
bash deploy/gcloud/provision.sh
bash deploy/gcloud/deploy-api.sh
firebase projects:addfirebase hisobchi-509915
bash deploy/gcloud/deploy-frontend.sh
bash deploy/gcloud/deploy-bot.sh
bash deploy/gcloud/verify.sh
```

Skip `projects:addfirebase` if the project is already enabled for Firebase.
`provision.sh` asks for the Telegram token without echoing it on first setup;
it also accepts `BOT_TOKEN` from the process environment. Do not put tokens in
shell command arguments or commit them. An existing secret is reused.

The scripts perform the following work:

1. Enable APIs, create runtime/build identities, Cloud SQL, database/user,
   Secret Manager credentials, and Artifact Registry. Reruns reuse existing
   resources and passwords; they do not reset database users or overwrite secrets.
2. Upload only allowed backend source files, build the Python 3.13 image, and pin
   its digest and secret versions. Run `alembic upgrade head` as a Cloud Run Job.
   A failed migration stops API deployment. Deploy the API with public HTTP access;
   business endpoints still require validated Telegram `initData`.
3. Build React with the actual API URL plus `/api/v1` and publish `dist/`.
   Firebase provides HTTPS and the React router fallback. API CORS allows only
   the configured frontend origin.
4. Create the VM, upload an archive excluding `.env`, virtual environments, and
   test files, install Python/uv/proxy, and fetch secrets using the attached VM
   identity. Systemd runs one polling bot and the proxy as an unprivileged user.
   A separate migration unit handles the root-owned environment file correctly.

`backend/.dockerignore` and `.gcloudignore` both exclude credentials. The image
runs as an unprivileged user and honors Cloud Run's `PORT`. The API uses the
Cloud SQL Unix socket; the bot uses the proxy on `127.0.0.1:5432`. PostgreSQL
does not need an authorized public client network.
Each bot/API process defaults to two pooled database connections and one overflow
connection, keeping the small database's connection usage bounded. These can be
adjusted with `DATABASE_POOL_SIZE` and `DATABASE_MAX_OVERFLOW` after upgrading.

The runtime service account can connect to Cloud SQL and read only the three
application secrets. A separate build account has the standard Cloud Build
builder role. No downloaded service-account keys are needed.

## Telegram and final verification

Stop any other process polling the same bot token before starting the VM bot.
Send `/start`, then use **Ilovani ochish** to open the Mini App. Optionally set
the same Hosting URL in BotFather's menu button settings. A normal browser
without Telegram credentials cannot sign into the production app.

Check that an attendance record survives closing and reopening the Mini App,
and that records made through the bot appear in the Mini App. These live user
checks cannot be replaced by `/health`, which tests liveness only. The successful
migration job separately proves connectivity to PostgreSQL.

Test boot recovery after deployment:

```bash
source deploy/gcloud/common.sh
gc compute ssh "$VM_NAME" --zone="$ZONE" --command='sudo reboot' || true
# Wait for the VM to boot, then:
bash deploy/gcloud/verify.sh
```

The unfinished bot form state is in memory and resets on restart; confirmed
records persist in PostgreSQL. Cloud SQL backups should also be restore-tested
before relying on the app for irreplaceable business records.

## Updates and operations

Run `deploy-api.sh` for API changes, `deploy-frontend.sh` for React changes, and
`deploy-bot.sh` for bot changes. The bot update stops its service before replacing
code and restarts it only after migrations succeed. Do not run simultaneous
deployments. Use backwards-compatible schema migrations because the old API/bot
can still be running while the migration job executes.
If a build succeeds but a later deployment step fails, reuse that image with
`DEPLOY_IMAGE=asia-south2-docker.pkg.dev/PROJECT_ID/hisobchi/api:TAG bash deploy/gcloud/deploy-api.sh`.

```bash
source deploy/gcloud/common.sh
gc run services logs read "$RUN_SERVICE" --region="$REGION" --limit=100
gc run jobs executions list --job="$RUN_SERVICE-migrate" --region="$REGION"
gc compute ssh "$VM_NAME" --zone="$ZONE"
# Inside the VM:
sudo systemctl status cloud-sql-proxy hisobchi-bot
sudo journalctl -u hisobchi-bot -n 100 --no-pager
sudo journalctl -u hisobchi-migrate -n 100 --no-pager
sudo systemctl restart hisobchi-bot
```

Bot files are in `/opt/hisobchi/backend`; credentials are root-owned, mode 600,
at `/etc/hisobchi/bot.env`. Systemd reads that file before dropping privileges.
Do not `source` it as the login user. To rerun migrations on the VM:
`sudo systemctl start hisobchi-migrate`.

For credential rotation, update the database user if needed, add matching secret
versions, and redeploy both API and bot. They do not refresh secret values
automatically. Do not overwrite the stored password and rerun provisioning as
a rotation procedure. Keep API and bot token versions consistent.

The VM assumes an existing `default` VPC/subnet with outbound internet and SSH
access; set `NETWORK`/`SUBNET` if your project uses another network. No app or DB
ports are opened. Organizational policies may require IAP-based SSH or prohibit
public Cloud Run access; resolve those policies with your project administrator.

## References

- [Cloud Run container contract](https://docs.cloud.google.com/run/docs/container-contract)
- [Cloud SQL creation options](https://docs.cloud.google.com/sdk/gcloud/reference/sql/instances/create)
- [Cloud SQL Auth Proxy](https://docs.cloud.google.com/sql/docs/postgres/sql-proxy)
- [Cloud Build user-specified identities](https://docs.cloud.google.com/build/docs/securing-builds/configure-user-specified-service-accounts)
- [Firebase CLI](https://firebase.google.com/docs/cli)
- [Firebase SPA rewrites](https://firebase.google.com/docs/hosting/full-config)
