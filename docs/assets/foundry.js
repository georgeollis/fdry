(() => {
  "use strict";

  document.querySelectorAll("pre:not([data-no-copy])").forEach((pre) => {
    const code = pre.querySelector("code");
    if (!code || !navigator.clipboard) return;
    const wrapper = document.createElement("div");
    wrapper.className = "fd-code-block";
    pre.before(wrapper);
    wrapper.append(pre);
    const button = document.createElement("button");
    button.type = "button";
    button.className = "fd-copy";
    button.textContent = "Copy";
    button.setAttribute("aria-label", "Copy code to clipboard");
    const status = document.createElement("span");
    status.className = "visually-hidden";
    status.setAttribute("role", "status");
    button.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(code.textContent.trimEnd());
        button.textContent = "Copied";
        status.textContent = "Code copied to clipboard.";
      } catch {
        button.textContent = "Select code";
        status.textContent = "Clipboard unavailable. Select and copy the code manually.";
      }
      window.setTimeout(() => { button.textContent = "Copy"; }, 2000);
    });
    wrapper.append(button, status);
  });

  document.querySelectorAll("main table").forEach((table) => {
    const wrapper = document.createElement("div");
    wrapper.className = "fd-table-scroll";
    wrapper.tabIndex = 0;
    wrapper.setAttribute("role", "region");
    wrapper.setAttribute("aria-label", "Scrollable reference table");
    table.before(wrapper);
    wrapper.append(table);
  });

  document.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
      const modal = document.getElementById("mkdocs_search_modal");
      if (!modal || !window.bootstrap) return;
      event.preventDefault();
      bootstrap.Modal.getOrCreateInstance(modal).show();
    }
  });
})();
