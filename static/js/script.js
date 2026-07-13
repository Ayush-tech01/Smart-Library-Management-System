/* ═══════════════════════════════════════════════════════════════════════
   LibraryOS — Main JavaScript
   ═══════════════════════════════════════════════════════════════════════ */

/* ── Sidebar toggle ─────────────────────────────────────────────────────── */
const sidebar        = document.getElementById('sidebar');
const sidebarToggle  = document.getElementById('sidebarToggle');
const sidebarOverlay = document.getElementById('sidebarOverlay');

if (sidebarToggle) {
    sidebarToggle.addEventListener('click', () => toggleSidebar());
}
if (sidebarOverlay) {
    sidebarOverlay.addEventListener('click', () => toggleSidebar(false));
}
function toggleSidebar(force) {
    const open = force !== undefined ? force : !sidebar.classList.contains('open');
    sidebar.classList.toggle('open', open);
    sidebarOverlay.classList.toggle('open', open);
    document.body.style.overflow = open ? 'hidden' : '';
}

/* ── Modal system ───────────────────────────────────────────────────────── */
function openModal(id) {
    const m = document.getElementById(id);
    if (m) m.classList.add('open');
}
function closeModal(id) {
    const m = document.getElementById(id);
    if (m) m.classList.remove('open');
}

// Open via data-modal attribute
document.querySelectorAll('[data-modal]').forEach(btn => {
    btn.addEventListener('click', () => openModal(btn.dataset.modal));
});
// Close via data-close attribute
document.querySelectorAll('[data-close]').forEach(btn => {
    btn.addEventListener('click', () => closeModal(btn.dataset.close));
});
// Close on backdrop click
document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
    backdrop.addEventListener('click', e => {
        if (e.target === backdrop) backdrop.classList.remove('open');
    });
});
// Close on Escape
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal-backdrop.open').forEach(m => m.classList.remove('open'));
    }
});

/* ── Toast notification system ──────────────────────────────────────────── */
let toastContainer = document.getElementById('toast-container');
if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toast-container';
    document.body.appendChild(toastContainer);
}

function showToast(message, type = 'info', duration = 3500) {
    const icons = {
        success: 'check-circle',
        danger:  'exclamation-circle',
        warning: 'exclamation-triangle',
        info:    'info-circle'
    };
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <i class="fas fa-${icons[type] || 'info-circle'}" style="color:var(--${type === 'danger' ? 'red' : type === 'success' ? 'green' : type === 'warning' ? 'amber' : 'blue'})"></i>
        <span>${message}</span>`;
    toastContainer.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(40px)';
        toast.style.transition = 'all .3s';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/* ── Flash message auto-dismiss ─────────────────────────────────────────── */
document.querySelectorAll('.flash-msg').forEach(msg => {
    setTimeout(() => {
        msg.style.opacity = '0';
        msg.style.transform = 'translateY(-8px)';
        msg.style.transition = 'all .4s';
        setTimeout(() => msg.remove(), 400);
    }, 4500);
});

/* ── Active nav item highlight ──────────────────────────────────────────── */
const currentPath = window.location.pathname;
document.querySelectorAll('.nav-item').forEach(link => {
    const href = link.getAttribute('href');
    if (href && href !== '/' && currentPath.startsWith(href)) {
        link.classList.add('active');
    }
});

/* ── Notifications bell live update ────────────────────────────────────── */
// (badge is server-side rendered; no polling needed)

/* ── Book search (live, debounced) ─────────────────────────────────────── */
const searchInput = document.getElementById('searchInput');
if (searchInput) {
    let debounce;
    searchInput.addEventListener('input', () => {
        clearTimeout(debounce);
        debounce = setTimeout(async () => {
            const term = searchInput.value.trim();
            if (!term) return;
            try {
                const res  = await fetch(`/books/search?q=${encodeURIComponent(term)}`);
                const books = await res.json();
                // Only used if there's a live results container
                const container = document.getElementById('liveResults');
                if (container) {
                    container.innerHTML = books.map(b =>
                        `<a href="/books/${b.id}" class="live-result-item">
                            <strong>${b.title}</strong>
                            <span>${b.author}</span>
                        </a>`
                    ).join('') || '<div class="live-result-empty">No results</div>';
                }
            } catch (e) { /* silent fail */ }
        }, 300);
    });
}

/* ── Star rating interactivity (CSS handles most, this handles hover state) */
document.querySelectorAll('.star-rating-input label').forEach(lbl => {
    lbl.addEventListener('mouseenter', () => {
        // CSS :hover handles the gold color
    });
});

/* ── Generic confirm-delete protection ──────────────────────────────────── */
document.querySelectorAll('a[onclick*="confirm"]').forEach(a => {
    // already handled inline, no change needed
});

/* ── Number counter animation for stat cards ────────────────────────────── */
function animateCounter(el) {
    const target = parseInt(el.textContent.replace(/[^0-9]/g, ''), 10);
    if (isNaN(target) || target === 0) return;
    let start = 0;
    const duration = 800;
    const step = Math.ceil(target / (duration / 16));
    const timer = setInterval(() => {
        start = Math.min(start + step, target);
        el.textContent = el.dataset.prefix
            ? el.dataset.prefix + start
            : start;
        if (start >= target) clearInterval(timer);
    }, 16);
}

const statValues = document.querySelectorAll('.stat-value');
if (statValues.length) {
    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const el = entry.target;
                // Only animate if it's a pure number
                const text = el.textContent.trim();
                if (/^[\d,]+$/.test(text)) {
                    animateCounter(el);
                }
                observer.unobserve(el);
            }
        });
    }, { threshold: 0.3 });
    statValues.forEach(el => observer.observe(el));
}

/* ── Table row highlight on hover (enhanced) ─────────────────────────────  */
document.querySelectorAll('.data-table tbody tr').forEach(tr => {
    tr.addEventListener('mouseenter', () => tr.style.background = 'rgba(45,106,79,0.04)');
    tr.addEventListener('mouseleave', () => {
        if (!tr.classList.contains('row-overdue')) tr.style.background = '';
    });
});

/* ── Book cover error fallback ──────────────────────────────────────────── */
document.querySelectorAll('img[src*="openlibrary"]').forEach(img => {
    img.addEventListener('error', function() {
        const parent = this.parentElement;
        if (parent) {
            const icon = document.createElement('div');
            icon.className = this.classList.contains('txn-cover') ? 'no-cover-mini' : 'no-cover';
            icon.innerHTML = '<i class="fas fa-book"></i>';
            parent.replaceChild(icon, this);
        }
    });
});

/* ── Smooth page load ───────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
    document.body.style.opacity = '0';
    document.body.style.transition = 'opacity .25s';
    requestAnimationFrame(() => {
        document.body.style.opacity = '1';
    });
});