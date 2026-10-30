(() => {
  "use strict";

  const root = document.documentElement;
  const system = window.matchMedia("(prefers-color-scheme: dark)");
  let mode = root.getAttribute("data-bs-theme");
  try {
    const stored = localStorage.getItem("mkdocs-colormode");
    if (["light", "dark", "auto"].includes(stored)) mode = stored;
  } catch {
    // Theme controls must also work when browser storage is disabled.
  }

  const apply = () => {
    root.setAttribute("data-bs-theme", mode === "auto" ? (system.matches ? "dark" : "light") : mode);
    document.querySelectorAll("[data-bs-theme-value]").forEach((button) => {
      const selected = button.getAttribute("data-bs-theme-value") === mode;
      button.setAttribute("aria-pressed", String(selected));
      button.lastElementChild.classList.toggle("d-none", !selected);
      if (selected) {
        document.querySelector("#theme-menu i").className = button.firstElementChild.className;
      }
    });
  };
  document.querySelectorAll("[data-bs-theme-value]").forEach((button) => {
    button.addEventListener("click", () => {
      mode = button.getAttribute("data-bs-theme-value");
      try { localStorage.setItem("mkdocs-colormode", mode); } catch {}
      apply();
    });
  });
  system.addEventListener("change", () => { if (mode === "auto") apply(); });
  apply();
})();
