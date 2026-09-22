# Deploy and update — taksunusaspa.com

Two options. **Docker** is the recommended one; the **plain systemd** option is
there if the server has no Docker.

Throughout, the branch is `claude/taksunu-spa-website-updates-g6b4xn` — change
it if you merge the work into `main` later.

---

## A. First install (Docker)

```bash
# 1. Get the code
cd /opt
git clone -b claude/taksunu-spa-website-updates-g6b4xn \
  https://github.com/sabuj14eu/taksunuspa.git
cd taksunuspa

# 2. Configure
cp .env.example .env
nano .env
#    SECRET_KEY      -> paste the output of: openssl rand -hex 32
#    DB_PASSWORD     -> a strong password (used by both db and app)
#    SITE_URL        -> https://taksunusaspa.com
#    APP_PORT        -> 5200, or any free port if that one is taken
#    WHATSAPP_NUMBER -> the spa's WhatsApp, digits only
#    TELEGRAM_BOT_TOKEN / ADMIN_TELEGRAM_CHAT -> optional order alerts

# 2b. Check the port is free BEFORE starting. On a server that already runs
#     other services, a clash shows up as "Bind for 127.0.0.1:5200 failed:
#     port is already allocated".
sudo ss -lntp | grep ":$(grep '^APP_PORT=' .env | cut -d= -f2)" \
  && echo "PORT IN USE — pick another APP_PORT in .env" \
  || echo "port is free"

# 3. Build and start
docker compose up -d --build

# 4. Create the tables and the starting content
docker compose exec app python -m scripts.seed
#    This prints the admin phone and a generated password — copy them now.

# 5. Check it is answering
curl -I "http://127.0.0.1:$(grep '^APP_PORT=' .env | cut -d= -f2)/"
```

**If the port is already allocated**, nothing is broken — pick another and
restart. Nothing else needs to change except the nginx `proxy_pass` below:

```bash
sed -i 's|^APP_PORT=.*|APP_PORT=5310|' .env
docker compose up -d
```

### nginx + HTTPS

```bash
sudo nano /etc/nginx/sites-available/taksunusaspa.com
```

```nginx
server {
    listen 80;
    server_name taksunusaspa.com www.taksunusaspa.com;

    client_max_body_size 12M;   # photo uploads

    location / {
        # must match APP_PORT in .env
        proxy_pass http://127.0.0.1:5200;
        proxy_set_header Host              $host;
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/taksunusaspa.com /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d taksunusaspa.com -d www.taksunusaspa.com
```

Then sign in at `https://taksunusaspa.com/login` and change the password in
**Admin → My account**.

---

## B. Update the server after new code is pushed

This is the command you will use most often:

```bash
cd /opt/taksunuspa
git pull origin claude/taksunu-spa-website-updates-g6b4xn
docker compose up -d --build
docker compose exec app python -m scripts.migrate
docker compose logs --tail=40 app
```

`scripts/migrate.py` creates any new tables and adds any new columns. It never
drops anything, so it is safe to run on every deploy.

### Nothing is being sent — start here

Bookings save and guests see their confirmation whether or not any gateway is
configured. **Out of the box nothing is configured**, so no WhatsApp and no
e-mail leave the server. One command says exactly what is missing:

```bash
docker compose exec app python -m scripts.check_notifications
```

It prints what is on, the last ten send attempts with the reason each failed,
the last five bookings, and the exact `.env` lines to add. Test a real send
once configured:

```bash
docker compose exec app python -m scripts.check_notifications --send 6281236729448
docker compose exec app python -m scripts.check_notifications --send-email you@gmail.com
```

The Admin dashboard shows the same warning, and every skipped message is
recorded in **Admin → Alerts** with its reason.

The quickest channel to get working is **Telegram** — free, no verification,
about five minutes (see Alerts & Telegram in admin). E-mail needs an SMTP
login; with Gmail that is an app password, not your normal password. WhatsApp
to guests needs a provider account and, on Meta, an approved template.

### Booking notifications and WhatsApp

The website is the only place a booking is created, changed or cancelled.
WhatsApp and e-mail are notification channels hanging off that, and every one
of them is best-effort: if a gateway is down, the booking is still saved, the
guest still sees their confirmation page, and the failure is recorded in
Admin → Alerts. Nothing waits on WhatsApp approval to go live.

After a booking is saved the site sends:

| To | Channel | Contains |
|---|---|---|
| Customer | WhatsApp | code, service, date, time, address, status, manage link |
| Customer | e-mail | the same, if they gave an address |
| Owner | WhatsApp | the full booking including the customer's number |
| Owner | e-mail | the same |
| Therapist | WhatsApp or Telegram | the job and their fee |

The customer's message never carries a therapist's name or number, an admin
number, or any `wa.me` link — the only action it offers is the manage link
back to the website.

**Switching provider** is one line in `.env`. `WA_PROVIDER=meta` is the
production route; `fonnte` or `wablas` are a stopgap while Meta verification
and template approval are pending. No other file changes.

**Meta needs an approved template.** A confirmation goes to a guest who has
not messaged the spa first, so Meta treats it as business-initiated and will
only deliver a Utility template approved in advance. Create it in WhatsApp
Manager with seven parameters in the order listed in `.env.example`, then set
`WA_TEMPLATE_BOOKING`. Until that name is set the customer's WhatsApp is
skipped and the reason is logged — everything else still sends.

**It is not free.** Checked September 2026: Utility templates are billed per
message. They were free inside the 24-hour customer service window from
1 July 2025, but **from 1 October 2026 Meta charges for them inside that
window too**. Each business number gets 1,000 free service messages a month;
past that, every confirmation has a cost. Meta's own pricing page is the
authority — re-check it before budgeting.

### Updating the English wording

All the English copy lives in `scripts/copy_en.py` — the positioning line, the
service areas, treatment and product descriptions, About Us, Delivery &
Payment, the FAQ and the footer. Edit that file, then push it to the site:

```bash
docker compose exec app python -m scripts.apply_copy            # show changes
docker compose exec app python -m scripts.apply_copy --write    # apply them
```

It writes English text only — never a price, a duration, a slug, a photo, a
stock level or any Indonesian field — and it finishes by listing any retired
wording it found but did not write, so nothing is quietly left behind.

### One-off: fill in the missing Indonesian text

The treatment and treatment-group descriptions were seeded in English only, so
an Indonesian visitor read English there. Run this **once** after deploying.

The app code is baked into the image, not mounted from disk, so `git pull`
alone does not put a new script inside the container — rebuild first, or
`exec` fails with `No module named scripts.backfill_id`:

```bash
git pull origin claude/taksunu-spa-website-updates-g6b4xn
docker compose up -d --build                                     # required
docker compose exec app python -m scripts.backfill_id            # show
docker compose exec app python -m scripts.backfill_id --write    # apply
```

It covers treatments, treatment groups and product groups. It only writes into
a field that is empty, so anything you have typed in admin is left alone —
running it twice changes nothing, and it is safe to run again after any future
update in case new text has been added. It prints anything it has no
Indonesian for, which you then translate in Admin → Treatments or → Products.

Never run `scripts/seed.py` on the live site: unlike the backfill it overwrites
existing rows, so it would replace your edited prices and descriptions with the
starting ones. Seeding is for a brand-new database only.

As a one-liner:

```bash
cd /opt/taksunuspa && \
git pull origin claude/taksunu-spa-website-updates-g6b4xn && \
docker compose up -d --build && \
docker compose exec -T app python -m scripts.migrate && \
docker compose ps
```

### Other day-to-day commands

```bash
docker compose logs -f app          # follow the logs
docker compose restart app          # restart without rebuilding
docker compose down                 # stop everything
docker compose exec app bash        # shell inside the container

# Database backup (run before any risky change)
docker compose exec -T db pg_dump -U taksunusa taksunusa \
  > ~/backups/taksunusa-$(date +%F-%H%M).sql

# Restore
cat ~/backups/taksunusa-2026-09-12-1400.sql | \
  docker compose exec -T db psql -U taksunusa taksunusa
```

Uploaded photos live in the `uploads` Docker volume, so a rebuild does not
touch them. Back them up separately:

```bash
docker run --rm -v taksunuspa_uploads:/data -v ~/backups:/backup alpine \
  tar czf /backup/uploads-$(date +%F).tar.gz -C /data .
```

### Nightly backup cron

```bash
crontab -e
```

```cron
0 3 * * * cd /opt/taksunuspa && docker compose exec -T db pg_dump -U taksunusa taksunusa > ~/backups/taksunusa-$(date +\%F).sql 2>&1
```

---

## C. Plain systemd install (no Docker)

```bash
sudo apt update && sudo apt install -y python3-venv python3-pip nginx
cd /opt
sudo git clone -b claude/taksunu-spa-website-updates-g6b4xn \
  https://github.com/sabuj14eu/taksunuspa.git
sudo chown -R $USER:$USER taksunuspa
cd taksunuspa

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

cp .env.example .env && nano .env      # SECRET_KEY, DATABASE_URL, SITE_URL
set -a && . ./.env && set +a
.venv/bin/python -m scripts.seed
```

`/etc/systemd/system/taksunuspa.service`:

```ini
[Unit]
Description=Taksu Nusa Spa website
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/taksunuspa
EnvironmentFile=/opt/taksunuspa/.env
ExecStart=/opt/taksunuspa/.venv/bin/gunicorn -w 3 -b 127.0.0.1:5200 --timeout 60 wsgi:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now taksunuspa
sudo systemctl status taksunuspa
```

Update:

```bash
cd /opt/taksunuspa
git pull origin claude/taksunu-spa-website-updates-g6b4xn
.venv/bin/pip install -r requirements.txt
set -a && . ./.env && set +a
.venv/bin/python -m scripts.migrate
sudo systemctl restart taksunuspa
sudo journalctl -u taksunuspa -n 40 --no-pager
```

---

## D. If something breaks

| Symptom | Check |
|---|---|
| 502 from nginx | `docker compose ps` / `systemctl status taksunuspa` — is the app up? |
| App will not start | `SECRET_KEY` missing from `.env`. The app refuses to start without it, deliberately. |
| `No module named scripts.…` | The image is older than your files. `docker compose up -d --build`, then run the command again. |
| Login always fails | Set a new password directly — see below. Do **not** re-run `scripts.seed` on the live site; it overwrites treatments, prices and descriptions with the starting ones. |
| Uploads fail | `client_max_body_size 12M;` missing from the nginx block. |
| Prices look wrong | Admin → Discounts. An active site-wide discount applies to everything. |
| Sitemap missing a page | The item is inactive, or its group is. |

### Locked out of admin

Set a new password on the owner account without touching any content:

```bash
docker compose exec app python -c "
from app import create_app
from app.extensions import db
from app.models.user import User
app = create_app()
with app.app_context():
    u = User.query.filter_by(role='admin').order_by(User.id).first()
    u.set_password('choose-a-new-one-at-least-8-chars')
    u.is_active_flag = True
    db.session.commit()
    print('password reset for', u.phone)
"
```

Change the password in Admin → My account straight afterwards, so the one
typed on the command line does not stay in your shell history.

After any deploy, the quick check:

```bash
curl -sI https://taksunusaspa.com/ | head -1
curl -s  https://taksunusaspa.com/robots.txt
curl -s  https://taksunusaspa.com/sitemap.xml | head -c 300
```

### Tell Google about the site

Once live, in Google Search Console: add the property, verify it, and submit
`https://taksunusaspa.com/sitemap.xml`. Do the same in Bing Webmaster Tools.
