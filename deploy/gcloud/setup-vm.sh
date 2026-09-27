#!/usr/bin/env bash
# Invoked remotely by deploy-bot.sh on an Ubuntu 24.04 amd64 VM.
set -euo pipefail
set +x
[[ $EUID == 0 ]] || { echo 'Run as root.' >&2; exit 1; }
stage=${1:?Missing deployment staging directory}
# shellcheck source=/dev/null
source "$stage/vm.env"
export DEBIAN_FRONTEND=noninteractive
apt-get update
if [[ ! -d /opt/hisobchi/backend/.venv ]]; then
  apt-get upgrade -y
fi
apt-get install -y curl ca-certificates python3-venv
id hisobchi >/dev/null 2>&1 || useradd --system --home-dir /opt/hisobchi --shell /usr/sbin/nologin hisobchi
python3 -m venv /opt/hisobchi-tools
/opt/hisobchi-tools/bin/pip install --disable-pip-version-check uv==0.12.13
export UV_PYTHON_INSTALL_DIR=/opt/hisobchi-python
/opt/hisobchi-tools/bin/uv python install 3.13

curl --fail --silent --show-error --location --retry 3 \
  "https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v${PROXY_VERSION}/cloud-sql-proxy.linux.amd64" \
  -o "$stage/cloud-sql-proxy"
install -m 755 "$stage/cloud-sql-proxy" /usr/local/bin/cloud-sql-proxy
/usr/local/bin/cloud-sql-proxy --version
install -d -m 755 /opt/hisobchi/backend
install -d -m 700 /etc/hisobchi

# Read secrets via the VM's attached identity, without service-account key files.
export PROJECT_ID FRONTEND_URL
python3 - <<'PY'
import base64
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

req = Request('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token',
              headers={'Metadata-Flavor': 'Google'})
with urlopen(req, timeout=30) as response:
    token = json.load(response)['access_token']

def secret(name):
    url = f'https://secretmanager.googleapis.com/v1/projects/{os.environ["PROJECT_ID"]}/secrets/{name}/versions/latest:access'
    req = Request(url, headers={'Authorization': f'Bearer {token}'})
    with urlopen(req, timeout=30) as response:
        return base64.b64decode(json.load(response)['payload']['data']).decode()

values = {
    'APP_ENV': 'production',
    'BOT_TOKEN': secret('hisobchi-bot-token'),
    'DATABASE_URL': secret('hisobchi-bot-database-url'),
    'TIMEZONE': 'Asia/Tashkent',
    'CORS_ORIGINS': os.environ['FRONTEND_URL'],
    'MINI_APP_URL': os.environ['FRONTEND_URL'],
    'DEV_TELEGRAM_USER_ID': '',
}
if any('\n' in v or '\r' in v for v in values.values()):
    raise SystemExit('Environment values must not contain line breaks')
path = Path('/etc/hisobchi/bot.env.new')
fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
with os.fdopen(fd, 'w') as out:
    out.write(''.join(f'{k}={json.dumps(v)}\n' for k, v in values.items()))
path.replace('/etc/hisobchi/bot.env')
PY

# Updating a live installation: stop the sole poller before replacing code.
if systemctl cat hisobchi-bot.service >/dev/null 2>&1; then
  systemctl stop hisobchi-bot
fi
rm -rf /opt/hisobchi/backend/app /opt/hisobchi/backend/alembic
tar -xzf "$stage/backend.tar.gz" -C /opt/hisobchi/backend
cd /opt/hisobchi/backend
/opt/hisobchi-tools/bin/uv sync --locked --no-dev --python 3.13
chmod -R a+rX /opt/hisobchi/backend /opt/hisobchi-python

cat > /etc/systemd/system/cloud-sql-proxy.service <<EOF
[Unit]
Description=Hisobchi Cloud SQL Auth Proxy
After=network-online.target
Wants=network-online.target

[Service]
User=hisobchi
ExecStart=/usr/local/bin/cloud-sql-proxy --address=127.0.0.1 --port=5432 ${INSTANCE_CONNECTION_NAME}
Restart=always
RestartSec=5
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/hisobchi-migrate.service <<'EOF'
[Unit]
Description=Hisobchi database migrations
After=network-online.target cloud-sql-proxy.service
Requires=cloud-sql-proxy.service

[Service]
Type=oneshot
User=hisobchi
WorkingDirectory=/opt/hisobchi/backend
EnvironmentFile=/etc/hisobchi/bot.env
Environment=PYTHONDONTWRITEBYTECODE=1
ExecStart=/opt/hisobchi/backend/.venv/bin/alembic upgrade head
TimeoutStartSec=300
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
EOF

cat > /etc/systemd/system/hisobchi-bot.service <<'EOF'
[Unit]
Description=Hisobchi Telegram polling bot
After=network-online.target cloud-sql-proxy.service
Wants=network-online.target
Requires=cloud-sql-proxy.service
StartLimitIntervalSec=0

[Service]
Type=simple
User=hisobchi
WorkingDirectory=/opt/hisobchi/backend
EnvironmentFile=/etc/hisobchi/bot.env
Environment=PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
ExecStart=/opt/hisobchi/backend/.venv/bin/python -m app.bot.main
Restart=always
RestartSec=5
TimeoutStopSec=30
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable cloud-sql-proxy hisobchi-bot
systemctl restart cloud-sql-proxy
# Wait for the proxy listener before migration; Alembic proves DB connectivity.
python3 - <<'PY'
import socket
import time
for attempt in range(30):
    try:
        with socket.create_connection(('127.0.0.1', 5432), timeout=1):
            break
    except OSError:
        time.sleep(1)
else:
    raise SystemExit('Cloud SQL proxy did not start')
PY
systemctl start hisobchi-migrate
systemctl restart hisobchi-bot
systemctl is-active cloud-sql-proxy hisobchi-bot
rm -rf -- "$stage"
