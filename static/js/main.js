/* Shared client-side helpers for SmartHR */
(function () {
  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function formatNumber(value) {
    const numeric = Number(value);
    if (Number.isNaN(numeric)) {
      return value ?? "";
    }
    return numeric.toLocaleString("en-IN");
  }

  async function requestJson(url, options = {}) {
    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      ...options,
    });

    let data = {};
    try {
      data = await response.json();
    } catch (error) {
      data = {};
    }

    if (!response.ok) {
      const message = data.error || data.message || "Request failed";
      throw new Error(message);
    }

    return data;
  }

  function setActiveNavLink() {
    const currentPath = window.location.pathname;
    document.querySelectorAll(".sidebar .nav-link").forEach((link) => {
      const href = link.getAttribute("href");
      const isActive = href === currentPath || (currentPath.startsWith("/employees") && href === "/employees") || (currentPath.startsWith("/leaves") && href === "/leaves") || (currentPath.startsWith("/chatbot") && href === "/chatbot") || (currentPath.startsWith("/feedback") && href === "/feedback");
      link.classList.toggle("active", isActive);
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    setActiveNavLink();
    document.body.classList.add("fade-in-up");
  });

  window.SmartHR = {
    escapeHtml,
    formatNumber,
    requestJson,
    setActiveNavLink,
  };
})();
