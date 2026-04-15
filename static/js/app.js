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
        primary: d ? '#3B82F6' : '#2563EB',
        primaryA: function(a) { return d ? 'rgba(59,130,246,'+a+')' : 'rgba(37,99,235,'+a+')'; },
        secondary: d ? '#22D3EE' : '#0891B2',
        secondaryA: function(a) { return d ? 'rgba(34,211,238,'+a+')' : 'rgba(8,145,178,'+a+')'; },
        blueA: function(a) { return d ? 'rgba(96,165,250,'+a+')' : 'rgba(59,130,246,'+a+')'; },
        purpleA: function(a) { return d ? 'rgba(167,139,250,'+a+')' : 'rgba(124,58,237,'+a+')'; },
        amberA: function(a) { return d ? 'rgba(251,191,36,'+a+')' : 'rgba(217,119,6,'+a+')'; },
        text: d ? '#6B7280' : '#64748B',
        grid: d ? 'rgba(255,255,255,0.04)' : 'rgba(15,23,42,0.05)',
        tip: {
            bg: d ? '#141414' : '#fff',
            title: d ? '#F1F5F9' : '#0f172a',
            body: d ? '#94A3B8' : '#475569',
            border: d ? 'rgba(255,255,255,0.08)' : '#e2e8f0'
        },
        card: d ? '#0d0d0d' : '#ffffff',
        palette: d
            ? ['#3B82F6','#22D3EE','#FBBF24','#F87171','#A78BFA','#34D399','#FB7185','#9CA3AF']
            : ['#2563EB','#0891B2','#D97706','#dc2626','#7C3AED','#059669','#E11D48','#64748b'],
        // Build vertical gradient for area/bar fill
        makeGradient: function(ctx, colorTop, alpha) {
            var h = ctx.canvas.offsetHeight || 280;
            var g = ctx.createLinearGradient(0, 0, 0, h);
            g.addColorStop(0, colorTop.replace('1)', alpha+')'));
            g.addColorStop(1, colorTop.replace('1)', '0)'));
            return g;
        }
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


// ═══════════════════════════════════════════════════════
//  Notification system — native macOS + in-app panel
// ═══════════════════════════════════════════════════════

var _notifLastId = 0;
var _notifPanelOpen = false;

// Icon map for notification panel
var NOTIF_ICONS = {
    party: '🎉', user: '👤', heart: '❤️', send: '📨', task: '☑️', info: 'ℹ️'
};

// ── Request native notification permission on load ──
(function() {
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
})();

// ── Send a native macOS notification ──
function sendOSNotification(title, body) {
    if (!('Notification' in window)) return;
    if (Notification.permission !== 'granted') {
        Notification.requestPermission().then(function(p) {
            if (p === 'granted') new Notification(title, { body: body, icon: '/static/css/favicon.png' });
        });
        return;
    }
    new Notification(title, { body: body || '', icon: '/static/css/favicon.png' });
}

// ── Toggle notification panel ──
function toggleNotifPanel() {
    var panel = document.getElementById('notifPanel');
    _notifPanelOpen = !_notifPanelOpen;
    if (_notifPanelOpen) {
        panel.classList.add('open');
        fetchNotifications();
    } else {
        panel.classList.remove('open');
    }
}

// Close panel on outside click
document.addEventListener('click', function(e) {
    var wrapper = document.getElementById('notifWrapper');
    if (wrapper && _notifPanelOpen && !wrapper.contains(e.target)) {
        document.getElementById('notifPanel').classList.remove('open');
        _notifPanelOpen = false;
    }
});

// ── Time ago helper ──
function timeAgo(iso) {
    var diff = (Date.now() - new Date(iso).getTime()) / 1000;
    if (diff < 60) return 'Ahora';
    if (diff < 3600) return Math.floor(diff / 60) + ' min';
    if (diff < 86400) return Math.floor(diff / 3600) + ' h';
    return Math.floor(diff / 86400) + ' d';
}

// ── Render notifications in panel ──
function renderNotifications(data) {
    var list = document.getElementById('notifList');
    var badge = document.getElementById('notifBadge');

    // Update badge
    if (data.unread_count > 0) {
        badge.style.display = 'flex';
        badge.textContent = data.unread_count > 99 ? '99+' : data.unread_count;
    } else {
        badge.style.display = 'none';
    }

    if (!data.notifications || data.notifications.length === 0) {
        list.innerHTML = '<div class="notif-empty">Sin notificaciones</div>';
        return;
    }

    var html = '';
    data.notifications.forEach(function(n) {
        var icon = NOTIF_ICONS[n.icon] || 'ℹ️';
        html += '<div class="notif-item' + (n.read ? '' : ' unread') + '" onclick="markRead(' + n.id + ', this)">'
            + '<div class="notif-item-icon ' + n.icon + '">' + icon + '</div>'
            + '<div class="notif-item-body">'
            + '<div class="notif-item-title">' + n.title + '</div>'
            + (n.body ? '<div class="notif-item-text">' + n.body + '</div>' : '')
            + '<div class="notif-item-time">' + timeAgo(n.created_at) + '</div>'
            + '</div></div>';
    });
    list.innerHTML = html;
}

// ── Fetch notifications from server ──
function fetchNotifications() {
    fetch('/notifications/api?since_id=' + _notifLastId)
        .then(function(r) { return r.json(); })
        .then(function(data) {
            // Fire native OS notifications for truly new items
            if (data.notifications && data.notifications.length > 0) {
                var newest = data.notifications[0];
                if (newest.id > _notifLastId && _notifLastId > 0) {
                    // Only OS-notify for items newer than what we already saw
                    data.notifications.forEach(function(n) {
                        if (n.id > _notifLastId && !n.read) {
                            sendOSNotification('Madness Light — ' + n.title, n.body);
                        }
                    });
                }
                _notifLastId = newest.id;
            }
            renderNotifications(data);
        })
        .catch(function() {});
}

// ── Mark single notification as read ──
function markRead(id, el) {
    fetch('/notifications/api/read/' + id, { method: 'POST' })
        .then(function() {
            if (el) el.classList.remove('unread');
            fetchNotifications();
        });
}

// ── Mark all as read ──
function markAllRead() {
    fetch('/notifications/api/read-all', { method: 'POST' })
        .then(function() { fetchNotifications(); });
}

// ── Check task reminders and fire OS notifications ──
function checkTaskReminders() {
    fetch('/tareas/api/due-reminders')
        .then(function(r) { return r.json(); })
        .then(function(data) {
            if (data.due && data.due.length > 0) {
                data.due.forEach(function(t) {
                    sendOSNotification(
                        'Tarea pendiente',
                        t.title + (t.description ? ' — ' + t.description : '')
                    );
                });
            }
        })
        .catch(function() {});
}

// ── Polling loop ──
(function startPolling() {
    // Initial fetch
    fetchNotifications();
    checkTaskReminders();

    // Poll notifications every 30 seconds
    setInterval(fetchNotifications, 30000);

    // Check task reminders every 60 seconds
    setInterval(checkTaskReminders, 60000);
})();
