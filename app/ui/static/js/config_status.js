/**
 * ILLUM AI STUDIO — Local Desktop Runtime
 * UI Secret Status & Validation Feedback (P02-T05, ADR-001, DEC-003, DEC-007)
 * 
 * Invariants:
 * 1. Zero raw secrets exposed or stored in JS / browser memory.
 * 2. Connection tests run ONLY on explicit user clicks (no automatic page-load triggers).
 * 3. Never declare CONNECTED unless backend returns connected=true with HTTP 200.
 */

document.addEventListener("DOMContentLoaded", () => {
  const btnTestAll = document.getElementById("btn-test-all");
  const testButtons = document.querySelectorAll(".btn-test-provider");
  const activityLog = document.getElementById("activity-log");

  function logActivity(text, level = "info") {
    if (!activityLog) return;
    const timeStr = new Date().toLocaleTimeString();
    const entry = document.createElement("div");
    entry.className = "flex items-start gap-2 text-xs font-mono py-1 border-b border-zinc-800 last:border-0";
    
    let colorClass = "text-zinc-400";
    if (level === "success") colorClass = "text-emerald-400";
    if (level === "error") colorClass = "text-rose-400";
    if (level === "warn") colorClass = "text-amber-400";

    entry.innerHTML = `<span class="text-zinc-600">[${timeStr}]</span> <span class="${colorClass}">${escapeHtml(text)}</span>`;
    activityLog.prepend(entry);
  }

  function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/[&<>"']/g, (m) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;"
    }[m]));
  }

  function setBadgeState(badgeEl, state, connected) {
    if (!badgeEl) return;
    badgeEl.className = "px-2.5 py-1 text-xs font-semibold rounded-full border transition-colors ";
    
    if (connected || state === "CONNECTED") {
      badgeEl.className += "bg-emerald-950/70 text-emerald-300 border-emerald-600/50";
      badgeEl.textContent = "CONNECTED (200 OK)";
    } else if (state === "NOT_CONFIGURED") {
      badgeEl.className += "bg-zinc-800 text-zinc-400 border-zinc-700";
      badgeEl.textContent = "NOT CONFIGURED";
    } else if (state === "INVALID_CREDENTIALS") {
      badgeEl.className += "bg-rose-950/70 text-rose-300 border-rose-600/50";
      badgeEl.textContent = "INVALID CREDENTIALS (401)";
    } else if (state === "ACCESS_DENIED") {
      badgeEl.className += "bg-amber-950/70 text-amber-300 border-amber-600/50";
      badgeEl.textContent = "ACCESS FORBIDDEN (403)";
    } else if (state === "RATE_LIMITED") {
      badgeEl.className += "bg-yellow-950/70 text-yellow-300 border-yellow-600/50";
      badgeEl.textContent = "RATE LIMITED (429)";
    } else if (state === "UNAVAILABLE") {
      badgeEl.className += "bg-purple-950/70 text-purple-300 border-purple-600/50";
      badgeEl.textContent = "UNAVAILABLE / TIMEOUT";
    } else if (state === "INVALID_FORMAT") {
      badgeEl.className += "bg-rose-950/70 text-rose-300 border-rose-600/50";
      badgeEl.textContent = "INVALID FORMAT / PLACEHOLDER";
    } else {
      badgeEl.className += "bg-zinc-800 text-zinc-400 border-zinc-700";
      badgeEl.textContent = state || "NOT TESTED";
    }
  }

  function updateProviderUI(provider, res) {
    const card = document.getElementById(`provider-card-${provider}`);
    if (!card) return;

    const badge = card.querySelector(".connection-badge");
    const latencyEl = card.querySelector(".latency-val");
    const feedbackEl = card.querySelector(".feedback-text");
    const maskedKeyEl = card.querySelector(".masked-key-val");

    setBadgeState(badge, res.state, res.connected);

    if (latencyEl) {
      if (res.latency_ms !== null && res.latency_ms !== undefined) {
        latencyEl.textContent = `${Math.round(res.latency_ms)} ms`;
      } else {
        latencyEl.textContent = "—";
      }
    }

    if (feedbackEl) {
      feedbackEl.textContent = res.message || "—";
      if (res.connected) {
        feedbackEl.className = "feedback-text text-xs text-emerald-400 mt-1 font-mono";
      } else if (res.state === "NOT_CONFIGURED") {
        feedbackEl.className = "feedback-text text-xs text-zinc-400 mt-1 font-mono";
      } else {
        feedbackEl.className = "feedback-text text-xs text-rose-400 mt-1 font-mono";
      }
    }

    if (maskedKeyEl && res.masked_key) {
      maskedKeyEl.textContent = res.masked_key;
    }

    // Log to activity feed
    const statusLabel = res.connected ? "CONNECTED" : (res.state || "FAILED");
    const latStr = res.latency_ms ? ` (${Math.round(res.latency_ms)}ms)` : "";
    const logType = res.connected ? "success" : (res.state === "NOT_CONFIGURED" ? "info" : "error");
    logActivity(`${provider.toUpperCase()}: ${statusLabel}${latStr} — ${res.message || ""}`, logType);
  }

  async function testSingleProvider(provider, buttonEl) {
    if (!provider) return;
    const originalText = buttonEl ? buttonEl.innerHTML : "";
    if (buttonEl) {
      buttonEl.disabled = true;
      buttonEl.innerHTML = `<span class="inline-block animate-spin mr-1">⟳</span> Testing...`;
    }

    logActivity(`Testing connection to ${provider}...`, "info");

    try {
      const resp = await fetch(`/api/providers/${encodeURIComponent(provider)}/test-connection`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });

      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`);
      }

      const data = await resp.json();
      updateProviderUI(provider, data);
    } catch (err) {
      updateProviderUI(provider, {
        provider: provider,
        state: "UNAVAILABLE",
        connected: false,
        message: `Network error or server unreachable: ${err.message}`,
        latency_ms: null,
      });
      logActivity(`${provider.toUpperCase()} test failed: ${err.message}`, "error");
    } finally {
      if (buttonEl) {
        buttonEl.disabled = false;
        buttonEl.innerHTML = originalText;
      }
    }
  }

  async function testAllProviders() {
    if (!btnTestAll) return;
    const origHtml = btnTestAll.innerHTML;
    btnTestAll.disabled = true;
    btnTestAll.innerHTML = `<span class="inline-block animate-spin mr-1">⟳</span> Testing All Providers...`;

    // Disable all individual buttons
    testButtons.forEach((b) => (b.disabled = true));
    logActivity("Initiating connection tests for all providers...", "info");

    try {
      const resp = await fetch("/api/providers/test-connection", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });

      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`);
      }

      const data = await resp.json();
      const connections = data.connections || {};

      for (const [provider, res] of Object.entries(connections)) {
        updateProviderUI(provider, res);
      }
      logActivity("Finished testing all configured providers.", "success");
    } catch (err) {
      logActivity(`Batch test error: ${err.message}`, "error");
    } finally {
      btnTestAll.disabled = false;
      btnTestAll.innerHTML = origHtml;
      testButtons.forEach((b) => (b.disabled = false));
    }
  }

  // Bind single test buttons
  testButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const provider = btn.getAttribute("data-provider");
      testSingleProvider(provider, btn);
    });
  });

  // Bind test-all button
  if (btnTestAll) {
    btnTestAll.addEventListener("click", () => {
      testAllProviders();
    });
  }

  logActivity("Ready. Click 'Test Connection' on any provider to probe status.", "info");
});
