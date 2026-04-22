(function () {
  const root = document.getElementById("notification-root");
  if (!root) {
    return;
  }

  const bell = document.getElementById("notification-bell");
  const badge = document.getElementById("notification-badge");
  const dropdown = document.getElementById("notification-dropdown");
  const list = document.getElementById("notification-list");
  const emptyState = document.getElementById("notification-empty");
  const markAllButton = document.getElementById("mark-all-read");
  const toastStack = document.getElementById("notification-toast-stack");
  const listUrl = root.dataset.listUrl;
  const readUrl = root.dataset.readUrl;
  const readAllUrl = root.dataset.readAllUrl;
  let audioEnabled = false;

  function getCsrfToken() {
    const value = document.cookie
      .split("; ")
      .find((row) => row.startsWith("csrftoken="));
    return value ? value.split("=")[1] : "";
  }

  function updateBadge(unreadCount) {
    badge.textContent = unreadCount;
    badge.classList.toggle("hidden", unreadCount === 0);
  }

  function formatDate(value) {
    return new Date(value).toLocaleString([], {
      year: "numeric",
      month: "short",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function renderEmptyState() {
    emptyState.classList.toggle("hidden", list.children.length > 0);
  }

  function createItem(notification, prepend) {
    const item = document.createElement("button");
    item.type = "button";
    item.className = "notification-item flex w-full gap-3 border-b border-slate-100 px-4 py-3 text-left hover:bg-slate-50";
    if (!notification.is_read) {
      item.classList.add("bg-sky-50/70");
    }
    item.dataset.id = notification.id;
    item.innerHTML = `
      <span class="mt-1 inline-flex h-2.5 w-2.5 flex-none rounded-full ${notification.is_read ? "bg-slate-300" : "bg-sky-500"}"></span>
      <span class="min-w-0 flex-1">
        <span class="block text-sm text-slate-800"></span>
        <span class="mt-1 block text-xs text-slate-500">${formatDate(notification.created_at)}</span>
      </span>
    `;
    item.querySelector(".text-sm").textContent = notification.message;
    item.addEventListener("click", function () {
      markRead([notification.id], item);
    });

    if (prepend) {
      list.prepend(item);
    } else {
      list.appendChild(item);
    }
  }

  function renderList(notifications) {
    list.innerHTML = "";
    notifications.forEach((notification) => createItem(notification, false));
    renderEmptyState();
  }

  function showToast(notification) {
    const toast = document.createElement("div");
    toast.className = "pointer-events-auto rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-lg";
    toast.innerHTML = `
      <div class="flex items-start gap-3">
        <div class="mt-0.5 text-lg">🔔</div>
        <div class="min-w-0 flex-1">
          <p class="text-sm font-semibold text-slate-900">${notification.type_display}</p>
          <p class="mt-1 text-sm text-slate-600"></p>
        </div>
      </div>
    `;
    toast.querySelector(".text-slate-600").textContent = notification.message;
    toastStack.prepend(toast);
    window.setTimeout(function () {
      toast.remove();
    }, 4500);
  }

  function playAlertSound() {
    if (audioEnabled) {
      const context = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = context.createOscillator();
      const gain = context.createGain();
      oscillator.connect(gain);
      gain.connect(context.destination);
      oscillator.type = "sine";
      oscillator.frequency.value = 880;
      gain.gain.setValueAtTime(0.08, context.currentTime);
      oscillator.start();
      oscillator.stop(context.currentTime + 0.12);
    }
  }

  function markRead(notificationIds, item) {
    fetch(readUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify({ notification_ids: notificationIds }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (item) {
          item.classList.remove("bg-sky-50/70");
          const dot = item.querySelector(".rounded-full");
          if (dot) {
            dot.className = "mt-1 inline-flex h-2.5 w-2.5 flex-none rounded-full bg-slate-300";
          }
        }
        updateBadge(data.unread_count || 0);
      })
      .catch(() => {});
  }

  function fetchNotifications() {
    fetch(listUrl, {
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
    })
      .then((response) => response.json())
      .then((data) => {
        renderList(data.notifications || []);
        updateBadge(data.unread_count || 0);
      })
      .catch(() => {});
  }

  bell.addEventListener("click", function () {
    audioEnabled = true;
    dropdown.classList.toggle("hidden");
    if (!dropdown.classList.contains("hidden")) {
      fetchNotifications();
    }
  });

  markAllButton.addEventListener("click", function () {
    fetch(readAllUrl, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCsrfToken(),
      },
    })
      .then((response) => response.json())
      .then((data) => {
        list.querySelectorAll(".notification-item").forEach((item) => {
          item.classList.remove("bg-sky-50/70");
          const dot = item.querySelector(".rounded-full");
          if (dot) {
            dot.className = "mt-1 inline-flex h-2.5 w-2.5 flex-none rounded-full bg-slate-300";
          }
        });
        updateBadge(data.unread_count || 0);
      })
      .catch(() => {});
  });

  list.querySelectorAll(".notification-item").forEach((item) => {
    item.addEventListener("click", function () {
      markRead([item.dataset.id], item);
    });
  });

  document.addEventListener("click", function (event) {
    if (!root.contains(event.target)) {
      dropdown.classList.add("hidden");
    }
  });

  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${protocol}://${window.location.host}/ws/notifications/`);

  socket.onmessage = function (event) {
    const payload = JSON.parse(event.data);
    if (payload.type === "snapshot") {
      updateBadge(payload.unread_count || 0);
      return;
    }
    if (payload.type === "notification") {
      createItem(payload.notification, true);
      updateBadge(payload.unread_count || 0);
      renderEmptyState();
      showToast(payload.notification);
      playAlertSound();
    }
  };
})();
