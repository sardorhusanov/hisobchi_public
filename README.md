# Hisobchi — Telegram bot and Mini App

A small-business work manager in Uzbek. The bot handles quick daily operations;
the mobile Mini App provides management, history, reports, and charts. Both use
**the same services, models, and PostgreSQL database**.

Python 3.13 · uv · aiogram 3 · async SQLAlchemy · PostgreSQL · FastAPI · React ·
TypeScript · Vite · TanStack Query · Recharts. No Redis, Celery, or admin panel.
Local development needs no Docker. Google Cloud deployment uses a backend container;
see the [deployment guide and scripts](deploy/gcloud/README.md).

## What the project does

Hisobchi helps a small-business owner manage workers and partners, record daily
attendance, calculate salaries and advances, track project income and expenses,
and review financial reports. Each Telegram manager has a separate workspace.
The interface is in Uzbek, monetary amounts are displayed in Uzbek so'm, and
calendar dates use Asia/Tashkent.

The bot and API share the Python business services and database models. The bot
connects directly to PostgreSQL; the React Mini App calls the API over HTTPS.
Accounting calculations run on the backend.

| Component | Directory | Responsibility |
| --- | --- | --- |
| Telegram bot | `backend/app/bot` | aiogram long polling, message flows, Mini App launch |
| HTTP API | `backend/app/api` | FastAPI routes, Telegram authentication, workspace access |
| Shared backend | `backend/app/services`, `models`, `repositories` | Business rules and PostgreSQL persistence |
| Mini App | `miniapp` | React interface, forms, charts, reports |
| Deployment | `deploy/gcloud` | Google Cloud provisioning, releases, VM services, checks |

## Live application

Open [@hisobkitop_bot](https://t.me/hisobkitop_bot), send `/start`, and tap
**Ilovani ochish**. The [Mini App](https://hisobchi-509915.web.app) requires Telegram
launch credentials; opening its URL in a normal browser does not sign you in.
The [API health endpoint](https://hisobchi-api-dhqromlona-em.a.run.app/health)
checks that the API process is running.

Deployment details and the recorded checks are in
[deployment status](deploy/gcloud/DEPLOYMENT.md).

## Local setup

Prerequisites: Python 3.13, uv, a running PostgreSQL server, Node.js 22.12+ and npm.
For frontend utility tests, use Node.js 24+ (native TypeScript support).

### Database and backend

From the repository root (PostgreSQL package installation on Linux):

```bash
sudo -u postgres createuser --pwprompt work_management
sudo -u postgres createdb --owner=work_management work_management
cd backend
uv sync --locked
cp .env.example .env
```

Set `DATABASE_URL` in `.env` using the password entered above. Percent-encode
URL-special password characters. Get a bot token from BotFather for Telegram use.

```dotenv
BOT_TOKEN=your_bot_token
DATABASE_URL=postgresql+asyncpg://work_management:your_password@localhost:5432/work_management
DATABASE_POOL_SIZE=2
DATABASE_MAX_OVERFLOW=1
APP_ENV=development
LOG_LEVEL=INFO
TIMEZONE=Asia/Tashkent
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
MINI_APP_URL=
DEV_TELEGRAM_USER_ID=
TELEGRAM_AUTH_MAX_AGE=3600
```

From `backend/`:

```bash
uv run alembic upgrade head
uv run uvicorn app.api.main:app --reload --host 127.0.0.1 --port 8000
```

The API is at `http://127.0.0.1:8000/api/v1`. OpenAPI documentation is at `/docs`;
`/health` is an unauthenticated liveness check, not database readiness.
Alembic migrations in `backend/alembic/versions/` define the database schema.

### Telegram bot

In another terminal, from `backend/`:

```bash
uv run python -m app.bot.main
```

Use exactly one polling process per bot token. `/start` initializes the workspace
and owner. For local development while production is running, use a separate bot
token and database.

### Mini App

In another terminal, from the repository root:

```bash
cd miniapp
npm ci
cp .env.example .env
npm run dev
```

Frontend `.env`:

```dotenv
VITE_API_URL=http://127.0.0.1:8000/api/v1
VITE_DEV_AUTH=false
```

Only public settings belong in the frontend. **Never put BOT_TOKEN or a database
URL in a VITE_ variable.** Frontend environment variables are public build inputs.

## Testing outside Telegram

To use a normal local browser, explicitly enable both sides:

```dotenv
# backend/.env
APP_ENV=development
DEV_TELEGRAM_USER_ID=123456789

# miniapp/.env
VITE_DEV_AUTH=true
```

Restart both servers, then open `http://127.0.0.1:5173`. The API creates/uses the
workspace for the **server-configured** ID. Use your actual Telegram ID to share
local data with your bot, or a dedicated ID and test database for disposable data.

Development authentication requires all of: `APP_ENV=development`, a configured
positive `DEV_TELEGRAM_USER_ID`, the explicit `X-Dev-Auth: 1` header, a loopback
client connection, and an allowed Origin when present. No client-supplied user ID
is accepted. Invalid Telegram credentials never fall back to development login.
It is disabled for every other APP_ENV, including production. The frontend also
removes its development-header branch from production builds. Do not expose a
development server or proxy it to the public internet.

## Telegram authentication

The frontend sends `Telegram.WebApp.initData` in:

```http
Authorization: tma <raw initData>
```

This header is required on every business request; `POST /api/v1/auth/telegram`
validates it and returns the current account without issuing a separate token.
The backend:

1. Parses unique fields and removes `hash`.
2. Sorts the remaining fields into Telegram's data-check string.
3. Derives a secret with HMAC-SHA256 using `WebAppData` and the bot token.
4. Compares the expected hash using a constant-time comparison.
5. Validates `auth_date` (default maximum age 3,600 seconds, 30-second future skew).
6. Uses only the signed Telegram user ID to resolve/create the workspace.

Expired sessions show an Uzbek message asking the user to reopen the Mini App.
Credentials are not stored in localStorage, included in URLs, or logged by the app.
Treat initData as a bearer credential; serve everything over HTTPS in production.
Implementation follows [Telegram's validation specification](https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app).

All protected routes use `get_current_workspace`. Lookups, aggregates, histories,
and mutations are workspace-scoped. Composite foreign keys add protection against
cross-workspace references. Responses exclude internal workspace IDs. API request
transactions commit before success is sent; a failed batch rolls back entirely.

## Opening the Mini App from Telegram

1. Host the frontend on a public HTTPS URL, for example `https://app.example.com`.
2. Set backend `MINI_APP_URL=https://app.example.com` and restart the bot.
3. Send `/start` or use **Bosh menyu**. The bot sends **📱 Ilovani ochish** as an
   inline `WebAppInfo` button. Inline launch supports authenticated initData.
4. Optionally configure the bot's menu button with BotFather `/setmenubutton`, or
   configure its Main Mini App via `/mybots` → your bot → Bot Settings → Configure
   Mini App. Set the same HTTPS URL.

The app initializes `ready()`/`expand()`, follows Telegram light/dark theme changes,
and uses Telegram's BackButton on nested pages. Telegram WebApp launches should
be tested on a real device with your own bot token before release.

## Pages and behavior

Bottom navigation: **Bosh sahifa · Davomat · Loyihalar · Moliya · Ko'proq**.

- Dashboard: monthly totals, today's attendance progress, active projects, cash chart.
- Attendance: date selection, batch editing, “Hammasi 1 kun”, explicit save feedback;
  person/month view with full-day, half-day, and total summaries.
- Workers: monthly salary cards, creation, profile editing, salary change, deactivation.
- Partners: creation, editing, attendance and withdrawal history; no salary fields.
- Worker detail: overview, attendance calendar, advance history, month-selectable salary history.
- Salary: month/worker filters, backend-calculated totals and individual balances.
- Advances: salary-month/worker/project filters, creation, deletion with confirmation.
- Projects: active/completed lists, financial detail, description editing, paginated income
  and expense histories, new transactions, completion with confirmation.
- Finance: month, previous month or inclusive custom dates (maximum 366 days), separate
  business/owner/partner/other/advance totals, charts and filtered transaction history.
- Reports: monthly finance, attendance, salary, advances and project reports.
- Settings: owner name, Telegram account, version, timezone.

Money inputs support `6000000`, `6 000 000`, `6,000,000`, and up to two decimal
places. Monetary API values are decimal strings. React performs presentation and
input normalization only; monetary `Number` conversion is limited to drawing charts.
Transactions are paginated (30 default, 100 maximum); dashboard/chart aggregates
are computed server-side. Large people/project lists are intended for small teams.

## Business rules

- OWNER and PARTNER have attendance and no fixed salary; WORKER requires a positive salary.
- Salary = monthly salary / **30** × worked days, with one final gross rounding to
  cents (half up). Advances assigned to the salary month reduce remaining salary;
  negative remaining salary is allowed.
- Salary editing updates the existing single monthly rate. **Past reports are
  recalculated at that rate.** The UI explicitly asks for acknowledgement. Historical
  salary schedules are not stored.
- Missing attendance means zero. Only `1` and `0.5` are stored. `Yo'q` removes an
  entry. People are deactivated instead of deleting historical records.
- Finance cash flow counts advances by payment date, while salary/advance reports
  count them by assigned salary month. These can differ.
- Project balance = project income minus project expenses, including explicitly
  assigned owner/partner withdrawals. Salaries and advances do not automatically
  reduce project balance. General expenses are not allocated to a project.
- Completed projects remain readable but reject new income/expense entries.
- Calendar dates use Asia/Tashkent; audit timestamps represent timezone-aware UTC instants.
- One workspace per Telegram manager. The workspace model has no business-name field;
  Settings edits the owner display name.
- Bot FSM is in memory. Only unfinished forms disappear on restart; confirmed data
  persists. The Mini App always reloads confirmed server data.

## API endpoints

All business endpoints are under `/api/v1` and require authentication.
`month` uses `YYYY-MM`; dates use `YYYY-MM-DD`. `start` and `end` are inclusive in
requests and finance report responses. `active=false` includes archived people.

| Methods | Path | Purpose |
| --- | --- | --- |
| POST | `/auth/telegram` | Validate credentials; return identity |
| GET | `/me` | Current owner/account |
| GET | `/dashboard?month=` | Combined dashboard |
| GET, POST | `/people` | List/create people |
| GET, PATCH | `/people/{id}` | Detail/update/deactivate |
| GET, PUT | `/attendance` | Date view / atomic batch save |
| GET | `/attendance/monthly` | One person/month calendar |
| GET | `/attendance/report` | All people/month totals |
| GET | `/salaries` | Worker rows and totals |
| GET | `/salaries/{worker_id}` | Single salary calculation |
| GET, POST | `/advances` | Salary-month history/create |
| DELETE | `/advances/{id}` | Remove incorrect advance |
| GET, POST | `/projects` | List/create projects |
| GET, PATCH | `/projects/{id}` | Summary/update/complete |
| GET, POST | `/projects/{id}/income` | All-time paginated history/create |
| GET | `/projects/{id}/expenses` | All-time paginated expenses |
| GET, POST | `/expenses` | Period history/create expense or withdrawal |
| GET | `/finance/summary` | Totals and daily chart data |
| GET | `/finance/income` | Income history by payment date |
| GET | `/finance/advances` | Advances by payment date |
| GET | `/reports/monthly` | Monthly/custom-period finance report |
| GET | `/reports/projects/{id}` | All-time project report |

Histories accept `offset`/`limit`; relevant filters include `worker_id`, `person_id`,
`project_id`, and expense `category`. Full typed request/response contracts are in
OpenAPI `/docs`. Malformed input and inaccessible records produce safe Uzbek errors.

## Tests and checks

Backend, from `backend/`:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
```

The default run skips PostgreSQL tests. To run the full suite, use a separate,
migrated test database:

```bash
sudo -u postgres createdb --owner=work_management work_management_test
export TEST_DATABASE_URL='postgresql+asyncpg://work_management:your_password@localhost:5432/work_management_test'
DATABASE_URL="$TEST_DATABASE_URL" uv run alembic upgrade head
uv run pytest -q
DATABASE_URL="$TEST_DATABASE_URL" uv run alembic check
```

Backend tests cover deterministic salary/project calculations, Telegram signature
and expiry validation, development-mode restrictions, workspace isolation for reads
and writes, API workflows, atomic attendance rollback, aggregates, database
constraints, connection restart persistence, and bot flows including the launch button.

Frontend, from `miniapp/`:

```bash
npm run typecheck
npm run lint
npm test
npm run build
```

For the browser integration test, run the API on `127.0.0.1:8000` against a disposable
test database with development authentication enabled; run Vite on `127.0.0.1:5173`
with `VITE_API_URL=http://127.0.0.1:8000/api/v1` and `VITE_DEV_AUTH=true`. Then:

```bash
npx playwright install chromium
npm run test:e2e
```

Alternatively set `PLAYWRIGHT_CHROMIUM_EXECUTABLE` to an installed Chrome executable.
The browser test creates records in that test workspace and leaves them for inspection.
It checks actual API-backed flows and phone widths 320, 360, 390, 430px. Screenshots
and failure traces go in ignored `test-results/`. Do not run it against production.

## Verification

The 2026-09-27 deployment was checked with all 49 backend tests against a temporary
PostgreSQL database, frontend type checking and linting, four frontend unit tests,
and the Playwright browser/mobile integration test. The production container,
Cloud SQL migrations, API authentication boundary and CORS, Firebase SPA routing,
and bot recovery after a VM reboot were also verified.

See [deployment status](deploy/gcloud/DEPLOYMENT.md) for details and the remaining
manual Telegram save/reopen check. `/health` alone does not verify the database.

## Google Cloud deployment

| Component | Hosting | Initial configuration |
| --- | --- | --- |
| Bot | Compute Engine + systemd | One `e2-small` VM in `asia-south2-a` |
| API | Cloud Run | 1 CPU, 512 MiB, 0–2 instances, concurrency 40 |
| Database | Cloud SQL PostgreSQL 15 | `db-f1-micro`, single zone, 10 GB SSD with automatic growth |
| Mini App | Firebase Hosting | Static Vite build, HTTPS, SPA fallback |
| Credentials | Secret Manager | Bot token and separate API/bot database connection URLs |
| Images | Artifact Registry + Cloud Build | Backend container built from locked dependencies |

The API connects through Cloud Run's Cloud SQL Unix socket. The bot connects
through Cloud SQL Auth Proxy on the VM. Both use the same database and bot token.
Cloud Run and Firebase provide HTTPS; this setup needs no Nginx or Caddy.
The VM and database remain billable while the API scales to zero.

The repository includes deployment scripts; pushing to GitHub does **not**
automatically release changes. After the one-time project, billing, and login
setup described in the [deployment guide](deploy/gcloud/README.md):

```bash
# Run from the repository root after configuring deploy/gcloud/config.env.
bash deploy/gcloud/provision.sh
bash deploy/gcloud/deploy-api.sh
# Add Firebase to the existing Google Cloud project once before publishing.
bash deploy/gcloud/deploy-frontend.sh
bash deploy/gcloud/deploy-bot.sh
bash deploy/gcloud/verify.sh
```

The API release runs Alembic as a Cloud Run Job before deploying the new revision.
Bot releases install a single supervised polling process. Frontend releases build
with the deployed API URL. Database connections default to two pooled connections
plus one overflow connection per API/bot process.

Production uses `APP_ENV=production`, an empty `DEV_TELEGRAM_USER_ID`, and an
explicit HTTPS frontend origin in `CORS_ORIGINS`. Credentials and local environment
files are excluded from Git, container builds, and cloud source uploads. Cloud SQL
has daily backups with seven retained; restore procedures should also be tested.

## Deliberately postponed

Salary rate history with effective dates, payroll settlement, salary/project
allocation, multi-manager permissions, exports, income/expense editing or deletion,
project reopening, and a business-name field. These features are not implemented.

## Project structure

```text
backend/
  .env.example, pyproject.toml, uv.lock, alembic.ini
  Dockerfile, .dockerignore, .gcloudignore, cloudbuild.yaml
  alembic/{env.py,script.py.mako,versions/165fe4c96242_initial_workspace_and_business_schema.py}
  app/
    config/settings.py
    db/{base,session}.py
    models/entities.py
    repositories/{core,analytics}.py
    services/{core,miniapp,values}.py
    bot/{main,middleware,ui}.py
    bot/handlers/{common,attendance,flows,records,reports}.py
    api/
      main.py
      dependencies/{auth,workspace,filters}.py
      schemas/models.py
      routers/{overview,people,attendance,projects,finance}.py
  tests/{conftest,test_calculations,test_postgres,test_bot,test_auth,test_api}.py
miniapp/
  .env.example, .env.production.example, package.json, package-lock.json
  firebase.json
  index.html, tsconfig.json, vite.config.ts, eslint.config.js, playwright.config.ts
  src/
    app/{App,router,providers}.tsx
    api/{client,index}.ts
    telegram/webapp.ts
    hooks/data.ts
    types/{models.ts,telegram.d.ts}
    utils/{format.ts,format.test.ts}
    components/
      layout/Layout.tsx
      common/{ui,FinanceStats,ProjectCard,History,AttendanceCalendar,PeriodFilter}.tsx
      charts/FinanceCharts.tsx
      forms/{PersonForm,ProjectForm,TransactionForm}.tsx
    pages/{Dashboard,Attendance,Workers,WorkerDetails,Partners,Salary,Advances,
           Projects,ProjectDetails,Finance,Reports,Settings,More}.tsx
    main.tsx, style.css
  tests/miniapp.spec.ts
deploy/gcloud/
  README.md, DEPLOYMENT.md, config.env.example
  common.sh, provision.sh, deploy-api.sh, deploy-bot.sh
  setup-vm.sh, deploy-frontend.sh, verify.sh
```
