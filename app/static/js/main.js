// INFUX — main.js

// CSRF token helper
function csrfToken() {
    return document.querySelector('meta[name="csrf-token"]')?.content || '';
}

// Scroll-to-top
const scrollBtn = document.getElementById('scrollTop');
if (scrollBtn) {
    window.addEventListener('scroll', () => {
        scrollBtn.classList.toggle('show', window.scrollY > 300);
    });
    scrollBtn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
}

// Navbar scroll effect
const nav = document.getElementById('mainNav');
if (nav) {
    window.addEventListener('scroll', () => {
        nav.classList.toggle('scrolled', window.scrollY > 50);
    });
}

// Animated counters
document.querySelectorAll('[data-target]').forEach(el => {
    const target = parseInt(el.dataset.target);
    if (isNaN(target)) return;
    let current = 0;
    const step = Math.max(1, Math.floor(target / 60));
    const timer = setInterval(() => {
        current = Math.min(current + step, target);
        el.textContent = current.toLocaleString();
        if (current >= target) clearInterval(timer);
    }, 25);
});

// Discover page live search
const searchInput = document.getElementById('discoverSearch');
if (searchInput) {
    searchInput.addEventListener('input', () => {
        const q = searchInput.value.toLowerCase();
        const cards = document.querySelectorAll('.inf-card-wrap');
        let visible = 0;
        cards.forEach(card => {
            const show = card.textContent.toLowerCase().includes(q);
            card.style.display = show ? '' : 'none';
            if (show) visible++;
        });
        const info = document.getElementById('resultCount');
        if (info) info.textContent = q ? visible : cards.length;
    });
}

// Flash auto-dismiss
document.querySelectorAll('.alert-dismissible').forEach(alert => {
    setTimeout(() => {
        alert.style.transition = 'opacity .5s';
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 500);
    }, 4000);
});

// Confirm actions (works on both links and form submit buttons)
document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', e => {
        if (!confirm(el.dataset.confirm)) {
            e.preventDefault();
            e.stopImmediatePropagation();
        }
    });
    // Also intercept parent form submission when triggered via this button
    const form = el.closest('form');
    if (form && (el.type === 'submit' || el.tagName === 'BUTTON')) {
        form.addEventListener('submit', ev => {
            if (form._confirmOk) { form._confirmOk = false; return; }
            ev.preventDefault();
            if (confirm(el.dataset.confirm)) { form._confirmOk = true; form.submit(); }
        });
    }
});

// AOS init (gated on reduced-motion)
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
if (typeof AOS !== 'undefined') {
    AOS.init({ duration: reduceMotion ? 0 : 700, once: true, offset: 60, disable: reduceMotion });
}

// Form submit loading state — disable submit + show spinner (prevents double-submit).
// Skips forms whose submit button uses [data-confirm]. Uses safe DOM methods (no innerHTML).
document.querySelectorAll('form').forEach(f => {
    f.addEventListener('submit', () => {
        const b = f.querySelector('button[type="submit"], button:not([type])');
        if (b && !b.disabled && !b.dataset.confirm) {
            b.disabled = true;
            const saved = Array.from(b.childNodes); // detached but kept for restore
            const spinner = document.createElement('span');
            spinner.className = 'btn-spinner';
            b.replaceChildren(spinner, document.createTextNode(b.dataset.loading || 'Working…'));
            setTimeout(() => { b.disabled = false; b.replaceChildren(...saved); }, 8000); // failsafe
        }
    });
});
