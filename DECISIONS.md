# Free State Party — Decisions

Most recent wins. If something here contradicts older context, this is correct.

Last updated: February 15, 2026

---

## Project

- **What**: Landing page for the Free State Party — a private club for liberty-minded free staters in NH
- **Who runs it**: Jeremy Kauffman's crew. Dennis Pratt handles concierge/vetting (anonymous on site).
- **Domain**: freestate.party (Jeremy owns it)
- **Site**: https://freestate.party
- **Deploy from**: `git push production main` (post-receive hook on DO droplet)
- **Stack**: Markdown content → Python build script → multi-page static site + Tailwind CDN
- **Pages**: index.html (home), about.html, events.html, join.html

## Tone & Positioning

- **Confident, unapologetic, insider.** LPNH energy. Not defensive, not corporate.
- **"Across the room" register** — vibe based, feelings, we're not explaining, we're creating allure
- **Community "we" voice** — never "I", never individual names
- **Reactionary Futurism**: Past values (ambition, self-responsibility, greatness) + forward momentum (space age, techno-optimism). NOT nostalgic. NOT "return to" anything.
- **Assumes the reader already gets it** — doesn't explain libertarianism, doesn't hedge
- **Selective but not serious about it** — "We just want to know you're one of us"
- **No "application" language** — "introduce yourself and we'll reach out"

## Key Design Decisions

- **Multi-page architecture**: Jeremy wants separate pages, not single-page scroll. Home has hero + video, rest are separate pages.
- **JOIN button is bait**: Big gold button in nav and hero. Links to /join.html. You cannot join on the site. You have to come meet them in person.
- **Palette**: Exact same as Free State Saturdays
  - Background: #0a0a0a (dark-900)
  - Primary accent: #d4a017 (gold-500)
  - Gold light: #facc15 (gradients/hover)
  - Text hierarchy: #f8f8f8 / #b0b0b0 / #808080
  - Section alternation: #0a0a0a / #141414
- **Fonts**: Playfair Display (headlines) + Inter (body)
- **Video**: Ultra NH video embedded on home page (below hero)
- **Form**: Name, email/phone, "Tell us about yourself" free text, X handle (optional). Netlify Forms.
- **No logo**: Styled text wordmark for V1
- **No event photos yet**: Placeholder events, no imagery

## Content Architecture

All content in `content/*.md`. Non-technical collaborators edit markdown, run `python3 build.py`, deploy.

**Content and metadata are co-located.** Every page's title, description, og:image, and any other page-level config must live in the same `content/*.md` file as the page content — never in a separate file. Non-technical editors should only need to touch one file per page, without splitting unless there is a clear reason such as a content block being used across multiple pages.

Files: hero.md (home), about.md (about), events.md (events), rsvp.md (RSVP), footer.md, words.md

## What NOT to Do

- Don't use "application" or "apply" language
- Don't explain libertarianism to outsiders
- Don't be defensive about labels
- Don't use stock photos
- Don't make joining possible online
- Don't use corporate language or hedging
- Don't be nostalgic — forward momentum, not "return to"

## Expandability

- Monthly fee opportunity for Jeremy
- Brand expandable to cover liberty events statewide
- Content architecture (markdown files) supports adding event pages later
- Template structure supports multi-page expansion

## Still Open

1. Event photos — placeholder for now
2. Logo — styled text for V1
3. Upcoming events — placeholder events
4. ~~Netlify site ID~~ -- created: d3e99d3d-f171-43b7-8f20-8099bfa744bf
5. ~~DNS~~ — freestate.party points to DO droplet (147.182.191.226)
