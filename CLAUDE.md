# Free State Party — Site

## What This Is
Multi-page site for the Free State Party — a private club for liberty-minded free staters in NH. Dennis Pratt runs concierge/vetting (anonymous on site).

## Stack
- Multi-page output: `site/index.html`, `about/index.html`, `events/index.html`, `saturdays/index.html`
- Clean URLs via directory-based structure (e.g. `/about` serves `about/index.html`)
- Content in `content/*.md` (the CMS — edit content here)
- Shared template: `templates/base.html` with `{{placeholders}}`
- Build: `python3 build.py` reads content + base template, writes pages to `site/`
- Tailwind CSS via CDN, Google Fonts (Playfair Display + Inter), vanilla JS
- Forms to backend at app.freestate.party
- Auto-deploys from GitHub (`main` branch) → Digital Ocean droplet

## How to Edit Content
1. Edit the relevant `content/*.md` file
2. Run `python3 build.py`
3. Commit and push — Netlify auto-deploys from `main`

## Pages
- **/** — Home: hero with cycling word animation + video
- **/about** — About: pitch (identity/belonging) + what this is (clarity)
- **/events** — Events: tabbed open/closed
- **/saturdays** — Free State Saturdays: unlisted landing page with rotating poster image (not in nav)

## Directory Structure
```
content/          <- Markdown content files (the CMS)
  hero.md         <- Tagline, sub-tagline, CTA
  pitch.md        <- Identity/belonging section
  what-this-is.md <- Clarity section
  events.md       <- Open + closed events
  come-meet-us.md <- Join page copy
  footer.md       <- Footer content
  words.md        <- Cycling word list (one per line)
  saturdays.md    <- Free State Saturdays page content
templates/
  base.html       <- Shared HTML shell (nav, footer, head, scripts)
site/             <- Built output (deploy this dir)
  index.html      <- Home
  about/index.html  <- About
  events/index.html <- Events
  saturdays/index.html <- Free State Saturdays (unlisted)
  video/          <- Homepage video
  img/            <- Event/poster images
build.py          <- Build script
```

## Who Owns What
- **Content** (`content/*.md`): Anyone — edit markdown, build, push
- **Template/code** (`templates/`, `build.py`): Bill — structural changes, new pages, JS
- **Deploy config**: Bill — Netlify settings, domain DNS
- Use branches for anything beyond a simple content edit

## Design Decisions
See `DECISIONS.md` for the full list. Key points:
- **Palette**: dark-900 #0a0a0a + gold-500 #d4a017
- **Fonts**: Playfair Display (headlines) + Inter (body)
- **Voice**: Community "we", confident, unapologetic, LPNH energy
- **JOIN button**: Links to /saturdays (join form disabled for now). Cannot join online, must meet in person.
- **Reactionary Futurism**: Past values + forward momentum. Not nostalgic.

## Gotchas
- SVGs need explicit width/height HTML attributes (Tailwind preflight issue)
- No inline `style="..."` attributes (Netlify CSP blocks them) — use Tailwind classes
- Clean URLs via directory structure (`/about` → `about/index.html`)
- Links use relative paths with `{{base}}` prefix so local preview works
- Video is gitignored (too large) — `build.py` copies it from local source during build
- **Content and metadata are co-located**: a page's title, description, og:image, and all other page-level config must live in the same `content/*.md` file as its content — never in a separate file. Non-technical editors should only need to touch one file per page, without splitting unless there is a clear reason such as a content block being used across multiple pages.

## Domain & Hosting
- **Domain**: freestate.party
- **Hosting**: Digital Ocean (auto-deploy from GitHub `main`)
- **Repo**: github.com/kauffj/freestate.party
