/**
 * Founding Compact sign-on — data flow only.
 *
 * Reads the DOM contract defined by templates/founding-sign.html:
 *   #fsp-user-slot        — auth widget mount (filled by /embed/auth-widget.js)
 *   #signers-list         — container for live signers
 *   #sign-form            — sign form wrapper (hidden if not authorized to sign)
 *   #typed-name-input     — text input
 *   #sign-button          — submit button
 *   #doesnt-exist-view    — 404 view (hidden by default)
 *
 * Behavior: probe auth, fetch signers, render, poll every 3s, accept submit.
 * XSS-safe: textContent only. No innerHTML for user-supplied data.
 */
(function () {
    'use strict';

    // --- Config -------------------------------------------------------------

    var API_BASE = location.hostname === 'freestate.party'
        ? 'https://app.freestate.party'
        : 'http://localhost:3001';

    var GROUP_ID = 'grp_compact_signers';
    var AGREEMENT_SLUG = 'founding-compact';
    var POLL_INTERVAL_MS = 3000;

    // --- DOM lookups (resolved once at init) --------------------------------

    var els = null;

    function resolveElements() {
        var ids = [
            'fsp-user-slot',
            'signers-list',
            'sign-form',
            'typed-name-input',
            'sign-button',
            'doesnt-exist-view'
        ];
        var found = {};
        var missing = [];
        for (var i = 0; i < ids.length; i++) {
            var id = ids[i];
            var node = document.getElementById(id);
            if (!node) {
                missing.push(id);
            }
            found[id] = node || null;
        }
        if (missing.length) {
            console.warn('[founding-sign] missing DOM elements:', missing.join(', '));
        }
        return found;
    }

    // --- Pure helpers -------------------------------------------------------

    function formatTime(iso) {
        if (!iso) return '';
        var d = new Date(iso);
        if (isNaN(d.getTime())) return '';
        var hh = String(d.getHours()).padStart(2, '0');
        var mm = String(d.getMinutes()).padStart(2, '0');
        return hh + ':' + mm;
    }

    function hide(node) {
        if (node) node.hidden = true;
    }

    function show(node) {
        if (node) node.hidden = false;
    }

    // --- Render -------------------------------------------------------------

    function renderSigners(container, signers) {
        if (!container) return;
        // Full re-render — fine for ~30 names.
        container.textContent = '';
        for (var i = 0; i < signers.length; i++) {
            var s = signers[i];
            var row = document.createElement('div');
            row.className = 'signer';

            var nameEl = document.createElement('span');
            nameEl.className = 'signer-name';
            nameEl.textContent = s.name || s.typed_name || '';

            var timeEl = document.createElement('span');
            timeEl.className = 'signer-time';
            timeEl.textContent = formatTime(s.signed_at || s.created_at);

            row.appendChild(nameEl);
            row.appendChild(timeEl);
            container.appendChild(row);
        }
    }

    function renderInlineError(form, message) {
        if (!form) return;
        var existing = form.querySelector('.sign-error');
        if (existing) existing.remove();
        if (!message) return;
        var p = document.createElement('p');
        p.className = 'sign-error';
        p.setAttribute('role', 'alert');
        p.textContent = message;
        form.appendChild(p);
    }

    function renderSignedBadge(form) {
        if (!form) return;
        var existing = form.querySelector('.signed-badge');
        if (existing) return;
        var badge = document.createElement('div');
        badge.className = 'signed-badge';
        badge.textContent = 'You signed.';
        form.appendChild(badge);
    }

    function renderSignInCta(slot) {
        if (!slot) return;
        // The auth widget at /embed/auth-widget.js typically renders into this
        // slot. If we got here we either don't have the widget loaded or the
        // user is anon — give a plain link as a fallback CTA.
        if (slot.querySelector('.fsp-signin-cta')) return;
        var cta = document.createElement('a');
        cta.className = 'fsp-signin-cta';
        cta.href = API_BASE + '/sign-in?return=' + encodeURIComponent(location.href);
        cta.textContent = 'Sign in to add your name';
        slot.appendChild(cta);
    }

    // --- Network ------------------------------------------------------------

    function fetchJson(url, options) {
        var opts = options || {};
        opts.credentials = 'include';
        return fetch(url, opts).then(function (res) {
            return res.text().then(function (text) {
                var data = null;
                if (text) {
                    try { data = JSON.parse(text); } catch (e) { data = null; }
                }
                return { ok: res.ok, status: res.status, data: data };
            });
        });
    }

    function getMe() {
        return fetchJson(API_BASE + '/api/widget/me');
    }

    function getSigners() {
        return fetchJson(API_BASE + '/api/agreements/' + AGREEMENT_SLUG + '/signers');
    }

    function postSign(typedName) {
        return fetchJson(
            API_BASE + '/api/groups/' + GROUP_ID + '/rules/agreement',
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ typed_name: typedName })
            }
        );
    }

    // --- State derived from responses --------------------------------------

    function extractSigners(response) {
        if (!response || !response.data) return [];
        var d = response.data;
        if (Array.isArray(d)) return d;
        if (Array.isArray(d.signers)) return d.signers;
        if (Array.isArray(d.results)) return d.results;
        return [];
    }

    function extractUser(response) {
        if (!response || !response.ok || !response.data) return null;
        var d = response.data;
        return d.user || d.person || d || null;
    }

    function userHasSigned(user, signers) {
        if (!user || !signers || !signers.length) return false;
        var uid = user.id || user.person_id;
        var email = (user.email || '').toLowerCase();
        for (var i = 0; i < signers.length; i++) {
            var s = signers[i];
            if (uid && (s.person_id === uid || s.user_id === uid || s.id === uid)) return true;
            if (email && (s.email || '').toLowerCase() === email) return true;
        }
        return false;
    }

    // --- Polling ------------------------------------------------------------

    var pollTimer = null;

    function stopPolling() {
        if (pollTimer) {
            clearTimeout(pollTimer);
            pollTimer = null;
        }
    }

    function schedulePoll(fn) {
        stopPolling();
        pollTimer = setTimeout(fn, POLL_INTERVAL_MS);
    }

    // --- Submit handler -----------------------------------------------------

    function attachSubmit(state) {
        var btn = els['sign-button'];
        var input = els['typed-name-input'];
        var form = els['sign-form'];
        if (!btn || !input || !form) return;

        function submit() {
            var value = (input.value || '').trim();
            renderInlineError(form, '');
            if (!value) {
                input.focus();
                renderInlineError(form, 'Type your name to sign.');
                return;
            }
            btn.disabled = true;
            postSign(value).then(function (res) {
                if (res.ok) {
                    input.disabled = true;
                    btn.disabled = true;
                    renderSignedBadge(form);
                    // Force-refresh signers immediately.
                    refreshSigners(state, true);
                    return;
                }
                btn.disabled = false;
                if (res.status === 401) {
                    renderInlineError(form, 'Sign in to sign the compact.');
                    renderSignInCta(els['fsp-user-slot']);
                    return;
                }
                var msg = (res.data && (res.data.error || res.data.message))
                    || 'Could not save your signature. Try again.';
                renderInlineError(form, msg);
            }).catch(function (err) {
                btn.disabled = false;
                console.error('[founding-sign] submit failed', err);
                renderInlineError(form, 'Network error. Try again.');
            });
        }

        btn.addEventListener('click', function (e) {
            e.preventDefault();
            submit();
        });
        input.addEventListener('keydown', function (e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                submit();
            }
        });
    }

    // --- Refresh loop -------------------------------------------------------

    function refreshSigners(state, immediate) {
        getSigners().then(function (res) {
            if (res.status === 404) {
                // Not authorized / agreement not visible to this user.
                show(els['doesnt-exist-view']);
                hide(els['signers-list']);
                hide(els['sign-form']);
                stopPolling();
                return;
            }
            if (!res.ok) {
                console.warn('[founding-sign] signers fetch failed', res.status);
                schedulePoll(function () { refreshSigners(state); });
                return;
            }
            var signers = extractSigners(res);
            show(els['signers-list']);
            hide(els['doesnt-exist-view']);
            renderSigners(els['signers-list'], signers);

            // Show/hide form based on signed state.
            if (state.user) {
                if (userHasSigned(state.user, signers)) {
                    var form = els['sign-form'];
                    if (form) {
                        var input = els['typed-name-input'];
                        var btn = els['sign-button'];
                        if (input) input.disabled = true;
                        if (btn) btn.disabled = true;
                        renderSignedBadge(form);
                    }
                } else {
                    show(els['sign-form']);
                }
            } else {
                hide(els['sign-form']);
            }

            schedulePoll(function () { refreshSigners(state); });
        }).catch(function (err) {
            console.error('[founding-sign] signers fetch error', err);
            schedulePoll(function () { refreshSigners(state); });
        });
    }

    // --- Init ---------------------------------------------------------------

    function init() {
        els = resolveElements();

        // Default visible states (in case template defaults don't cover them).
        hide(els['doesnt-exist-view']);

        var state = { user: null };

        getMe().then(function (res) {
            state.user = extractUser(res);
            if (!state.user) {
                renderSignInCta(els['fsp-user-slot']);
                hide(els['sign-form']);
            }
            refreshSigners(state);
            attachSubmit(state);
        }).catch(function (err) {
            console.error('[founding-sign] auth probe failed', err);
            // Still try to load signers — they may be visible to anon.
            refreshSigners(state);
            attachSubmit(state);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
