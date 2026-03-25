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
        tip: { bg: d?'#111118':'#fafbfc', title: d?'#e2e8f0':'#0f172a', body: d?'#a0aec0':'#334155', border: d?'#2a2a3e':'#e0e4ea' },
        card: d ? '#0e0e16' : '#fafbfc',
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
