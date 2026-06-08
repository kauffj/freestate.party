# ⚠️ ARCHIVED — do not deploy

This repo is **retired**. The Free State Party marketing site was folded into the
**fsp-app** Next.js app and cut over at nginx on **2026-06-03**. The
`freestate.party` domain is now served by fsp-app, not by this static site.

This repo is kept only as a **content/asset archive and rollback reference**.

## What replaced it

- `freestate.party` (the root domain) is served by the fsp-app Next.js app. The
  former marketing pages are routes there: `/`, `/about`, `/business`, `/events`,
  `/visit`, `/founding`, `/saturday`.
- Page copy is now editable in-app via **`/admin/pages`** (a `pages` DB table),
  not by editing `content/*.md` + `build.py` here.
- Context: `fsp-app/docs/marketing-merge-handoff.md`,
  `fsp-app/docs/marketing-merge-remaining.md`, `fsp-app/docs/video-assets.md`.

## Do NOT

- **Do not redeploy this repo.** The deploy workflow (`.github/workflows/deploy.yml`)
  is disabled (`if: false`) and `build.py` is retired. Running either would push a
  dead static site over the live app's routes.
- **Do not trust `server-setup.sh` or `known-routes.conf`.** They describe the
  *old* nginx setup, which no longer matches the droplet — fsp-app rewired it
  (dropped the static `root`, repointed `/video/` to
  `/var/www/app.freestate.party/shared/video/`, symlinked `sites-enabled`). The
  old static webroot is parked at `/var/www/freestate.party.RETIRED-20260608`.

## Assets / videos

The videos are **gitignored** (`site/video/`) and the 1.1 GB 4K master
(`fs-party-4k.mp4`) lives only in this working tree — so a fresh clone does **not**
contain them. `homepage.mp4` (the live hero, an older encode whose recipe is lost)
was pulled to `site/video/homepage.mp4` as a verified copy. Durable archival of the
master + encode recipe is tracked in party-ops:
`back-up-4k-marketing-video-master-document-encode-` (@bargerwb).
