# Deployment status — 2026-09-27

Project: `hisobchi-509915` (billing enabled).

| Component | Result |
| --- | --- |
| Cloud SQL | `hisobchi-db`, PostgreSQL 15, `db-f1-micro`, Delhi; database `hisobchi` |
| Backups | Daily at 18:00 UTC, seven retained; automatic disk growth enabled |
| Secret Manager | Bot token, separate API/bot database URLs, generated database password |
| Artifact Registry | `asia-south2-docker.pkg.dev/hisobchi-509915/hisobchi` |
| Cloud Build | Build `83e3a8f5-0b01-4a26-a701-47a8b991fae3` succeeded |
| Migrations | Cloud Run execution `hisobchi-api-migrate-2gbsv` succeeded |
| API | https://hisobchi-api-dhqromlona-em.a.run.app |
| API revision | `hisobchi-api-00001-svq`, serving 100% of traffic |
| Bot VM | `hisobchi-bot`, `e2-small`, `asia-south2-a` |
| Telegram bot | https://t.me/hisobkitop_bot — polling started successfully |
| Firebase Hosting | Published at https://hisobchi-509915.web.app |
| Frontend build | Deployed, pointing at the production API |

Firebase activation succeeded and the frontend was published to the same Google
Cloud project. Use the [correct Firebase project](https://console.firebase.google.com/project/hisobchi-509915/overview).
The separately created `hisobchi-509915-64994` project is not used by this deployment.
The Telegram menu button is configured to open the production Mini App.

To update the frontend and check the deployment:

```bash
bash deploy/gcloud/deploy-frontend.sh
bash deploy/gcloud/verify.sh
```

Then send `/start` to the bot, open the Mini App, and verify saving/reopening a
record and sharing data between bot and Mini App. The production database was
created empty; local development data was not copied.

## Verification performed

- Backend: Ruff lint/format checks; all 49 tests passed against a temporary
  PostgreSQL database; Alembic reported no missing schema changes.
- Frontend: typecheck, ESLint, four unit tests, production build, and the real API
  Playwright browser/mobile integration test passed.
- Container: built successfully, runs as UID 10001, excludes `.env` files, and
  starts on the expected port.
- Cloud: PostgreSQL migrations succeeded; `/health` returned 200;
  unauthenticated `/api/v1/me` returned 401; CORS preflight accepted the intended
  Firebase origin.
- VM: SQL proxy and bot services started, are enabled at boot, and bot logs
  confirmed Telegram polling. Credentials are root-owned with permissions 600.
- Reboot recovery: rebooted the VM; both services returned to active state and
  exactly one bot polling process was running afterward.
- Production frontend bundle: contains the deployed API URL and excludes the
  development authentication header.
- Firebase: live HTML matches the production build, nested routes return the SPA,
  and the full deployment verification script passed. Telegram's menu button
  points at the live frontend. An actual user save/reopen test in Telegram remains.
- Deployment scripts: ShellCheck passed; cloud source upload excludes local
  credentials, virtual environments, caches, and tests.

See [README.md](README.md) for redeployment and maintenance commands.
