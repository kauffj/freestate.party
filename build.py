#!/usr/bin/env python3
"""
Free State Party — Build Script

Reads content/*.md files + templates/base.html, generates multi-page site.

Output:
  site/index.html  — Home (hero + video)
  site/about.html  — About (pitch + what this is)
  site/events.html — Events
  site/join.html   — Come Meet Us (concierge form)

Usage: python3 build.py
"""

import json
import os
import re
import shutil

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(SCRIPT_DIR, 'content')
TEMPLATE_DIR = os.path.join(SCRIPT_DIR, 'templates')
SITE_DIR = os.path.join(SCRIPT_DIR, 'site')


def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read().strip()


BASE_URL = 'https://freestate.party'


def extract_meta(text):
    """Extract top-level key: value metadata from a content file.
    Only reads non-indented, non-heading, non-list lines."""
    meta = {}
    for line in text.split('\n'):
        if line.startswith(' ') or line.startswith('\t') or line.startswith('-') or line.startswith('#'):
            continue
        if ':' in line:
            key, val = line.split(':', 1)
            if key.strip().isidentifier():
                meta[key.strip()] = val.strip()
    return meta


def _paragraphs_to_html(text):
    """Convert plain text to HTML paragraph tags."""
    html_parts = []
    for p in re.split(r'\n\s*\n', text.strip()):
        p = p.strip()
        if not p:
            continue
        p = re.sub(r'\*\*(.+?)\*\*', r'<strong class="text-dark-50">\1</strong>', p)
        p = re.sub(r'\*(.+?)\*', r'<em>\1</em>', p)
        p = p.replace(' — ', ' &mdash; ')
        p = p.replace('— ', '&mdash; ')
        html_parts.append(f'<p>{p}</p>')
    return '\n                '.join(html_parts)


def md_to_html(text):
    """Convert simple markdown to HTML. Returns (h2_title, body_html)."""
    lines = text.strip().split('\n')
    h2_title = ''
    body_lines = []
    skip_blank = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('# ') and not stripped.startswith('## '):
            skip_blank = True
            continue
        if stripped.startswith('## '):
            h2_title = stripped[3:].strip()
            skip_blank = True
            continue
        if skip_blank and stripped == '':
            skip_blank = False
            continue
        skip_blank = False
        body_lines.append(line)

    body_text = '\n'.join(body_lines).strip()
    # Skip metadata-only paragraphs
    filtered = []
    for p in re.split(r'\n\s*\n', body_text):
        if not all(re.match(r'^[a-z_]+:', line) for line in p.split('\n') if line.strip()):
            filtered.append(p)
    return h2_title, _paragraphs_to_html('\n\n'.join(filtered))


def parse_sections(text):
    """Parse a markdown file with metadata + multiple H2 sections.
    Returns (meta_dict, [(section_title, body_html), ...])."""
    meta = extract_meta(text)
    sections = []
    current_title = None
    current_lines = []
    past_meta = False

    for line in text.strip().split('\n'):
        stripped = line.strip()
        if stripped.startswith('# ') and not stripped.startswith('## '):
            past_meta = True
            continue
        if stripped.startswith('## '):
            if current_title is not None:
                sections.append((current_title, _paragraphs_to_html('\n'.join(current_lines))))
            current_title = stripped[3:].strip()
            current_lines = []
            past_meta = True
            continue
        if past_meta and current_title is not None:
            current_lines.append(line)

    if current_title is not None:
        sections.append((current_title, _paragraphs_to_html('\n'.join(current_lines))))

    return meta, sections


def parse_events(text):
    """Parse events.md into open and closed event lists. Returns (open_cards, closed_cards)."""
    lines = text.strip().split('\n')
    section = None  # 'open' or 'closed'
    events = {'open': [], 'closed': []}
    current = {}

    for line in lines:
        stripped = line.strip()
        if stripped.lower() == '## open events':
            section = 'open'
            continue
        elif stripped.lower() == '## closed events':
            if current and section:
                events[section].append(current)
                current = {}
            section = 'closed'
            continue
        elif stripped.startswith('# '):
            continue

        if stripped.startswith('- title:'):
            if current and section:
                events[section].append(current)
            current = {'title': stripped[8:].strip()}
        elif stripped.startswith('date:'):
            current['date'] = stripped[5:].strip()
        elif stripped.startswith('time:'):
            current['time'] = stripped[5:].strip()
        elif stripped.startswith('location:'):
            current['location'] = stripped[9:].strip()
        elif stripped.startswith('description:'):
            current['description'] = stripped[12:].strip()
        elif stripped.startswith('link:'):
            current['link'] = stripped[5:].strip()

    if current and section:
        events[section].append(current)

    def make_link(href):
        """Convert internal absolute links to use {{base}} for relative resolution."""
        if href.startswith('/'):
            return '{{base}}' + href
        return href

    def render_cards(event_list, is_open=False):
        cards = []
        for event in event_list:
            details = []
            if event.get('time'):
                details.append(event['time'])
            if event.get('location'):
                details.append(event['location'])
            details_html = ''
            if details:
                details_html = f'<p class="text-dark-400 text-sm mb-2">{" &bull; ".join(details)}</p>'

            link = make_link(event['link']) if event.get('link') else ''
            link_html = ''
            if link:
                link_html = f'<a href="{link}" class="inline-block mt-3 text-gold-500 hover:text-gold-400 text-sm font-medium transition-colors">Learn more &rarr;</a>'

            title_html = event.get('title', '')
            if link:
                title_html = f'<a href="{link}" class="hover:text-gold-500 transition-colors">{title_html}</a>'

            card = f'''<div class="bg-dark-900 border border-dark-600 rounded-lg p-6 hover:border-gold-700/50 transition-colors">
                    <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2 mb-3">
                        <h3 class="font-display text-xl font-bold text-dark-50">{title_html}</h3>
                        <span class="text-gold-500 font-medium text-sm whitespace-nowrap">{event.get("date", "")}</span>
                    </div>
                    {details_html}
                    <p class="text-dark-300 leading-relaxed">{event.get("description", "")}</p>
                    {link_html}
                </div>'''
            cards.append(card)
        return '\n                '.join(cards)

    return render_cards(events['open'], is_open=True), render_cards(events['closed'])


def parse_words(text):
    return [w.strip() for w in text.strip().split('\n') if w.strip()]


def build_page(base, page_title, page_description, og_title, page_content,
               page_scripts='', active_nav=None, is_subdir=False, base_path=None,
               og_url='', og_image=''):
    """Inject content into base template and return final HTML."""
    html = base
    html = html.replace('{{page_title}}', page_title)
    html = html.replace('{{page_description}}', page_description)
    html = html.replace('{{og_title}}', og_title)
    html = html.replace('{{og_url}}', og_url or BASE_URL)
    og_image_tag = f'<meta property="og:image" content="{BASE_URL}{og_image or "/img/og-default.png"}">'
    html = html.replace('{{og_image_tag}}', og_image_tag)
    html = html.replace('{{page_content}}', page_content)
    html = html.replace('{{page_scripts}}', page_scripts)

    # Relative base path: explicit base_path overrides is_subdir
    if base_path is not None:
        resolved_base = base_path
    else:
        resolved_base = '..' if is_subdir else '.'
    html = html.replace('{{base}}', resolved_base)

    # Nav active states
    for nav in ['about', 'events']:
        cls = 'nav-active' if active_nav == nav else 'text-dark-200'
        html = html.replace(f'{{{{nav_{nav}_class}}}}', cls)

    return html


def build():
    print("Building Free State Party site...")

    base = read_file(os.path.join(TEMPLATE_DIR, 'base.html'))

    # --- Read content ---
    hero_text = read_file(os.path.join(CONTENT_DIR, 'hero.md'))
    hero = extract_meta(hero_text)

    words = parse_words(read_file(os.path.join(CONTENT_DIR, 'words.md')))

    about_text = read_file(os.path.join(CONTENT_DIR, 'about.md'))
    about_meta, about_sections = parse_sections(about_text)

    events_text = read_file(os.path.join(CONTENT_DIR, 'events.md'))
    events_meta = extract_meta(events_text)
    open_events_html, closed_events_html = parse_events(events_text)


    # --- Page 1: Home (hero + video) ---
    home_content = f'''
    <section class="min-h-screen flex flex-col justify-center px-6 pt-20 pb-12 md:py-0">
        <div class="max-w-6xl mx-auto w-full lg:grid lg:grid-cols-2 lg:gap-12 lg:items-center">
            <div>
                <h1 class="font-display text-4xl sm:text-5xl md:text-6xl lg:text-5xl xl:text-6xl font-bold leading-tight mb-6">
                    <span class="text-dark-50">A private club for</span><br>
                    <span class="gold-gradient cycle-word" id="cycling-word" aria-live="polite">{words[0]}</span><br>
                    <span class="text-dark-50">free staters.</span>
                </h1>
                <p class="text-xl sm:text-2xl lg:text-xl xl:text-2xl text-dark-200 leading-relaxed max-w-2xl mb-10 font-display italic">
                    {hero.get('sub_tagline', 'We have a plan.')}
                </p>
                <a href="{{{{base}}}}/saturday/" class="inline-block bg-gold-500 hover:bg-gold-400 text-dark-900 font-bold text-lg px-10 py-4 rounded-lg transition-colors min-h-[48px]">
                    Meet Us
                </a>
            </div>
            <div class="mt-12 lg:mt-0">
                <div class="video-container shadow-2xl" id="video-wrapper">
                    <video id="hero-video" preload="metadata" playsinline>
                        <source src="{{{{base}}}}/video/homepage.mp4" type="video/mp4">
                    </video>
                    <button id="video-play" class="video-overlay" aria-label="Play video">
                        <svg width="72" height="72" viewBox="0 0 72 72" fill="none">
                            <circle cx="36" cy="36" r="35" stroke="#d4a017" stroke-width="2" fill="rgba(10,10,10,0.6)"/>
                            <polygon points="28,20 28,52 54,36" fill="#d4a017"/>
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    </section>'''

    home_scripts = f'''<script>
        const words = {json.dumps(words)};
        const el = document.getElementById('cycling-word');
        let currentIndex = 0;
        let paused = false;

        function cycleWord() {{
            if (paused) return;
            el.classList.add('fade-out');
            setTimeout(() => {{
                currentIndex = (currentIndex + 1) % words.length;
                el.textContent = words[currentIndex];
                el.classList.remove('fade-out');
            }}, 300);
        }}

        setInterval(cycleWord, 2500);

        document.addEventListener('visibilitychange', () => {{
            paused = document.hidden;
        }});

        // Video player
        const video = document.getElementById('hero-video');
        const playBtn = document.getElementById('video-play');
        if (video && playBtn) {{
            playBtn.addEventListener('click', () => {{
                playBtn.style.display = 'none';
                video.controls = true;
                video.play();
            }});
            video.addEventListener('ended', () => {{
                playBtn.style.display = 'flex';
                video.controls = false;
            }});
        }}
    </script>'''

    home_html = build_page(
        base,
        page_title=hero['title'],
        page_description=hero['description'],
        og_title=hero.get('og_title', hero['title']),
        page_content=home_content,
        page_scripts=home_scripts,
        active_nav=None,
        og_url=BASE_URL
    )

    # --- Page 2: About ---
    section_styles = ['px-6 pt-32 pb-20 md:pt-40 md:pb-28 bg-dark-800', 'px-6 py-20 md:py-28']
    about_sections_html = ''
    for i, (sec_title, sec_body) in enumerate(about_sections):
        style = section_styles[i] if i < len(section_styles) else 'px-6 py-20 md:py-28'
        about_sections_html += f'''
    <section class="{style}">
        <div class="max-w-3xl mx-auto">
            <div class="divider mb-6"></div>
            <h2 class="font-display text-3xl md:text-4xl font-bold text-dark-50 mb-10">{sec_title}</h2>
            <div class="space-y-6 text-lg text-dark-200 leading-relaxed">
                {sec_body}
            </div>
        </div>
    </section>'''

    about_content = about_sections_html + '''

    <section class="px-6 pb-20 md:pb-28 text-center">
        <a href="{{base}}/saturday/" class="inline-block bg-gold-500 hover:bg-gold-400 text-dark-900 font-bold text-lg px-10 py-4 rounded-lg transition-colors min-h-[48px]">
            Come Meet Us
        </a>
    </section>'''

    about_html = build_page(
        base,
        page_title=about_meta['title'],
        page_description=about_meta['description'],
        og_title=about_meta.get('og_title', about_meta['title']),
        page_content=about_content,
        active_nav='about',
        is_subdir=True,
        og_url=f'{BASE_URL}/about/'
    )

    # --- Page 3: Events (tabbed: open / closed) ---
    events_content = f'''
    <section class="px-6 pt-32 pb-20 md:pt-40 md:pb-28">
        <div class="max-w-3xl mx-auto">
            <div class="divider mb-6"></div>
            <h2 class="font-display text-3xl md:text-4xl font-bold text-dark-50 mb-8">Events</h2>

            <!-- Tabs -->
            <div class="flex gap-2 mb-10">
                <button id="tab-open" class="events-tab px-5 py-2.5 rounded-lg font-medium text-sm transition-colors bg-gold-500 text-dark-900" data-tab="open">
                    Open
                </button>
                <button id="tab-closed" class="events-tab px-5 py-2.5 rounded-lg font-medium text-sm transition-colors bg-dark-800 text-dark-300 hover:text-dark-100" data-tab="closed">
                    Members Only
                </button>
            </div>

            <!-- Open Events -->
            <div id="events-open" class="events-panel grid gap-6">
                {open_events_html}
            </div>

            <!-- Closed Events -->
            <div id="events-closed" class="events-panel hidden">
                <p class="text-2xl text-dark-200 font-display italic">Private.</p>
            </div>
        </div>
    </section>'''

    events_scripts = '''<script>
        document.querySelectorAll('.events-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                const target = tab.dataset.tab;

                // Toggle panels
                document.querySelectorAll('.events-panel').forEach(p => p.classList.add('hidden'));
                document.getElementById('events-' + target).classList.remove('hidden');

                // Toggle tab styles
                document.querySelectorAll('.events-tab').forEach(t => {
                    t.className = 'events-tab px-5 py-2.5 rounded-lg font-medium text-sm transition-colors bg-dark-800 text-dark-300 hover:text-dark-100';
                });
                tab.className = 'events-tab px-5 py-2.5 rounded-lg font-medium text-sm transition-colors bg-gold-500 text-dark-900';
            });
        });
    </script>'''

    events_html_page = build_page(
        base,
        page_title=events_meta['title'],
        page_description=events_meta['description'],
        og_title=events_meta.get('og_title', events_meta['title']),
        page_content=events_content,
        page_scripts=events_scripts,
        active_nav='events',
        is_subdir=True,
        og_url=f'{BASE_URL}/events/'
    )


    # --- Page 5: Saturdays (unlisted landing page) ---
    saturdays_text = read_file(os.path.join(CONTENT_DIR, 'saturdays.md'))
    saturdays_meta = extract_meta(saturdays_text)
    saturdays_title, saturdays_body = md_to_html(saturdays_text)

    sat_address = saturdays_meta.get('address', '')
    sat_maps_url = 'https://www.google.com/maps/search/' + sat_address.replace(' ', '+') if sat_address else ''
    sat_rsvp_url = saturdays_meta.get('rsvp_url', '')

    saturdays_content = f'''
    <section class="px-6 pt-32 pb-12 md:pt-40 md:pb-16">
        <div class="max-w-4xl mx-auto text-center">
            <div class="divider mb-6 mx-auto"></div>
            <h1 class="font-display text-4xl md:text-5xl lg:text-6xl font-bold text-dark-50 mb-6">{saturdays_title if saturdays_title else "Free State Saturdays"}</h1>
            <div class="space-y-4 text-lg text-dark-200 leading-relaxed max-w-2xl mx-auto">
                {saturdays_body}
            </div>
        </div>
    </section>

    <section class="px-6 pb-8 md:pb-10 text-center">
        <div class="flex flex-col sm:flex-row gap-4 justify-center">
            <a href="{sat_rsvp_url}" class="inline-flex items-center justify-center bg-gold-500 hover:bg-gold-400 text-dark-900 font-bold text-lg px-10 py-4 rounded-lg transition-colors min-h-[48px]">
                RSVP
            </a>
            <a href="{sat_maps_url}" target="_blank" rel="noopener" class="inline-flex items-center justify-center gap-2 bg-dark-700 hover:bg-dark-600 text-dark-100 font-bold text-lg px-10 py-4 rounded-lg transition-colors min-h-[48px]">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                Map
            </a>
        </div>
    </section>

    <section class="px-6 pb-8 md:pb-10">
        <div class="max-w-4xl mx-auto">
            <a href="{sat_maps_url}" target="_blank" rel="noopener" class="block select-none">
                <img src="{{{{base}}}}/img/saturdays-poster.jpg" alt="Free State Saturdays — this month's gathering"
                     class="w-full rounded-lg shadow-2xl hover:opacity-90 transition-opacity" style="max-height: min(80vh, 2000px); object-fit: contain;">
            </a>
        </div>
    </section>

    <section class="px-6 pb-20 md:pb-28 text-center">
        <div class="flex flex-col sm:flex-row gap-4 justify-center">
            <a href="{sat_rsvp_url}" class="inline-flex items-center justify-center bg-gold-500 hover:bg-gold-400 text-dark-900 font-bold text-lg px-10 py-4 rounded-lg transition-colors min-h-[48px]">
                RSVP
            </a>
            <a href="{sat_maps_url}" target="_blank" rel="noopener" class="inline-flex items-center justify-center gap-2 bg-dark-700 hover:bg-dark-600 text-dark-100 font-bold text-lg px-10 py-4 rounded-lg transition-colors min-h-[48px]">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                Map
            </a>
        </div>
    </section>'''

    saturdays_html = build_page(
        base,
        page_title=saturdays_meta['title'],
        page_description=saturdays_meta['description'],
        og_title=saturdays_meta.get('og_title', saturdays_meta['title']),
        page_content=saturdays_content,
        active_nav=None,
        is_subdir=True,
        og_url=f'{BASE_URL}/saturday/',
        og_image=saturdays_meta.get('og_image', '')
    )

    # --- Page 6: /saturday/rsvp/ redirect ---
    rsvp_redirect_html = f'''<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="0; url={sat_rsvp_url}">
<title>Redirecting...</title>
</head>
<body>
<script>window.location.replace("{sat_rsvp_url}");</script>
</body>
</html>'''

    # --- Write all pages ---
    # Root page stays as index.html; all others become <name>/index.html for clean URLs
    pages = {
        'index.html': home_html,
        'about/index.html': about_html,
        'events/index.html': events_html_page,
        'saturday/index.html': saturdays_html,
        'saturday/rsvp/index.html': rsvp_redirect_html,
    }

    for filepath, html in pages.items():
        full_path = os.path.join(SITE_DIR, filepath)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"  Built: site/{filepath}")

    # --- Copy video if not already present ---
    video_src = os.path.expanduser('~/Desktop/free-state-party-homepage-video.mp4')
    video_dst = os.path.join(SITE_DIR, 'video', 'homepage.mp4')
    if os.path.exists(video_src) and not os.path.exists(video_dst):
        os.makedirs(os.path.join(SITE_DIR, 'video'), exist_ok=True)
        shutil.copy2(video_src, video_dst)
        print("  Copied: video/homepage.mp4")

    print(f"\nDone. {len(pages)} pages built.")
    print(f"Words: {words}")


def watch():
    """Watch content/ and templates/ for changes, rebuild automatically."""
    import time

    watch_dirs = [CONTENT_DIR, TEMPLATE_DIR]

    def get_mtimes():
        mtimes = {}
        for d in watch_dirs:
            for root, _, files in os.walk(d):
                for f in files:
                    path = os.path.join(root, f)
                    mtimes[path] = os.path.getmtime(path)
        return mtimes

    print("Watching for changes... (Ctrl+C to stop)\n")
    build()
    last = get_mtimes()

    try:
        while True:
            time.sleep(0.5)
            current = get_mtimes()
            if current != last:
                changed = [p for p in current if current.get(p) != last.get(p)]
                for p in changed:
                    print(f"  Changed: {os.path.relpath(p, SCRIPT_DIR)}")
                print()
                build()
                print()
                last = current
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == '__main__':
    import sys
    if '--watch' in sys.argv or '-w' in sys.argv:
        watch()
    else:
        build()
