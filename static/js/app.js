// ─── Theme toggle ───────────────────────────────────
function isDark() { return document.documentElement.getAttribute('data-theme') === 'dark'; }

function toggleTheme() {
    var theme = isDark() ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('ml-theme', theme);
    window.dispatchEvent(new CustomEvent('themechange'));
}

function getChartTheme() {
    var d = isDark();
    return {
        primary: d ? '#89E900' : '#4F46E5',
        primaryA: function(a) { return d ? 'rgba(137,233,0,'+a+')' : 'rgba(79,70,229,'+a+')'; },
        secondary: d ? '#00f0ff' : '#14b8a6',
        secondaryA: function(a) { return d ? 'rgba(0,240,255,'+a+')' : 'rgba(20,184,166,'+a+')'; },
        indigoA: function(a) { return d ? 'rgba(167,139,250,'+a+')' : 'rgba(99,102,241,'+a+')'; },
        amberA: function(a) { return 'rgba(245,158,11,'+a+')'; },
        text: d ? '#a0aec0' : '#94a3b8',
        grid: d ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)',
        tip: { bg: d?'#2a2a2a':'#fafbfc', title: d?'#e2e8f0':'#0f172a', body: d?'#a0aec0':'#334155', border: d?'#2a2a3e':'#e0e4ea' },
        card: d ? '#1c1c1c' : '#fafbfc',
        palette: d
            ? ['#89E900','#00f0ff','#f59e0b','#ef4444','#a78bfa','#ec4899','#34d399','#64748b']
            : ['#4F46E5','#14b8a6','#f59e0b','#ef4444','#6366f1','#ec4899','#8b5cf6','#64748b']
    };
}

// ─── Modal helpers ──────────────────────────────────
function openModal(id) {
    document.getElementById(id).classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeModal(id) {
    document.getElementById(id).classList.remove('active');
    document.body.style.overflow = '';
}

// Close modal on overlay click (but not on click-drag from inside modal)
let modalMouseDownTarget = null;
document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('mousedown', (e) => {
        modalMouseDownTarget = e.target;
    });
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay && modalMouseDownTarget === overlay) {
            overlay.classList.remove('active');
            document.body.style.overflow = '';
        }
        modalMouseDownTarget = null;
    });
});

// Close modal on Escape
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay.active').forEach(m => {
            m.classList.remove('active');
        });
        document.body.style.overflow = '';
    }
});

// ─── Flash messages auto-dismiss ────────────────────
document.querySelectorAll('.flash-message').forEach(msg => {
    setTimeout(() => {
        msg.style.display = 'none';
    }, 4000);
});

// ─── Sidebar toggle for mobile ──────────────────────
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    sidebar.classList.toggle('open');
    overlay.classList.toggle('active');
}

// Close sidebar when clicking outside
document.addEventListener('click', (e) => {
    const sidebar = document.getElementById('sidebar');
    const hamburger = document.querySelector('.hamburger');
    const overlay = document.getElementById('sidebarOverlay');

    if (sidebar && sidebar.classList.contains('open') &&
        !sidebar.contains(e.target) &&
        hamburger && !hamburger.contains(e.target) &&
        e.target !== overlay) {
        sidebar.classList.remove('open');
        if (overlay) overlay.classList.remove('active');
    }
});

// Close sidebar when clicking a nav link (mobile UX)
document.querySelectorAll('.sidebar .nav-link').forEach(link => {
    link.addEventListener('click', () => {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebarOverlay');
        if (sidebar && window.innerWidth <= 768) {
            sidebar.classList.remove('open');
            if (overlay) overlay.classList.remove('active');
        }
    });
});
