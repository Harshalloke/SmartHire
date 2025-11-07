/* Theme toggle */
document.addEventListener("DOMContentLoaded", () => {
  const toggle = document.getElementById("themeToggle");
  if (toggle) {
    toggle.addEventListener("click", () => {
      document.documentElement.classList.toggle("light");
      localStorage.setItem("theme", document.documentElement.classList.contains("light") ? "light" : "dark");
    });
    // restore
    const pref = localStorage.getItem("theme");
    if (pref === "light") document.documentElement.classList.add("light");
  }

  /* Drag & Drop uploader on index */
  const drop = document.getElementById("dropArea");
  const input = document.getElementById("resume");
  const browseBtn = document.getElementById("browseBtn");
  const fileName = document.getElementById("fileName");

  if (browseBtn && input) {
    browseBtn.addEventListener("click", () => input.click());
  }

  if (drop && input) {
    const setName = (f) => fileName && (fileName.textContent = f ? f.name : "");
    drop.addEventListener("dragover", (e) => { e.preventDefault(); drop.classList.add("drop--over"); });
    drop.addEventListener("dragleave", () => drop.classList.remove("drop--over"));
    drop.addEventListener("drop", (e) => {
      e.preventDefault(); drop.classList.remove("drop--over");
      const f = e.dataTransfer.files[0];
      if (f) { input.files = e.dataTransfer.files; setName(f); }
    });
    input.addEventListener("change", () => setName(input.files[0]));
  }

  /* Radial gauge progressive fill (CSS is instant; this animates small pop) */
  const gauge = document.querySelector(".gauge");
  if (gauge) {
    const p = Number(gauge.getAttribute("data-progress") || 0);
    let cur = 0;
    const step = () => {
      cur += Math.max(1, Math.round((p - cur) * 0.12));
      gauge.style.setProperty("--p", cur);
      if (cur < p) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }

  /* Charts on result page */
  if (window.__RESULT__) {
    const r = window.__RESULT__;
    const overlap = (r.top_keywords || []).slice(0, 10);
    const missing = (r.missing_keywords || []).slice(0, 10);

    const bar = document.getElementById("matchBar");
    if (bar) {
      new Chart(bar.getContext("2d"), {
        type: "bar",
        data: {
          labels: ["Match %", "ATS Score"],
          datasets: [{
            label: "Score",
            data: [Number(r.match_percent || 0), Number(r.ats_score || 0)],
          }]
        },
        options: {
          responsive: true,
          scales: {
            y: { beginAtZero: true, max: 100 }
          },
          plugins: { legend: { display: false } }
        }
      });
    }

    const donut = document.getElementById("keywordsDonut");
    if (donut) {
      new Chart(donut.getContext("2d"), {
        type: "doughnut",
        data: {
          labels: ["Overlap", "Missing"],
          datasets: [{
            label: "Keywords",
            data: [overlap.length, missing.length],
          }]
        },
        options: {
          responsive: true,
          plugins: { legend: { position: "bottom" } },
          cutout: "60%"
        }
      });
    }
  }
});
/* -------- Custom Select Enhancer -------- */
function enhanceCustomSelect(rootId) {
  const root = document.getElementById(rootId);
  if (!root) return;
  const nativeId = root.getAttribute("data-for");
  const native = document.getElementById(nativeId);
  const btn = root.querySelector(".cselect__button");
  const list = root.querySelector(".cselect__list");
  const valueEl = root.querySelector(".cselect__value");
  const options = Array.from(root.querySelectorAll(".cselect__option"));

  const setOpen = (open) => {
    root.classList.toggle("cselect--open", open);
    btn.setAttribute("aria-expanded", String(open));
    if (open) {
      list.focus({ preventScroll: true });
      // set active to current selected
      const curVal = native ? native.value : "";
      const active = options.find(o => o.dataset.value === curVal) || options[0];
      options.forEach(o => o.classList.toggle("cselect__option--active", o === active));
      list.setAttribute("aria-activedescendant", active.id || "");
    }
  };

  const commit = (opt) => {
    const val = opt.dataset.value ?? "";
    const label = opt.textContent.trim();
    valueEl.textContent = label;
    options.forEach(o => o.setAttribute("aria-selected", String(o === opt)));
    if (native) {
      native.value = val;  // keeps form value in sync
      // also keep JD auto-fill behavior
      const jd = document.getElementById("job_description");
      const desc = opt.getAttribute("data-desc") || "";
      if (desc && jd && !jd.value.trim()) jd.value = desc;
    }
    setOpen(false);
  };

  // assign ids for aria
  options.forEach((o, i) => { if (!o.id) o.id = `${rootId}-opt-${i}`; });

  // initial label sync
  if (native && native.value) {
    const init = options.find(o => o.dataset.value === native.value);
    if (init) commit(init); else valueEl.textContent = "— Select a role —";
  }

  // interactions
  btn.addEventListener("click", () => setOpen(!root.classList.contains("cselect--open")));
  options.forEach(opt => {
    opt.addEventListener("click", () => commit(opt));
    opt.addEventListener("mouseenter", () => {
      options.forEach(o => o.classList.remove("cselect__option--active"));
      opt.classList.add("cselect__option--active");
    });
  });

  // keyboard nav
  const move = (dir) => {
    const idx = options.findIndex(o => o.classList.contains("cselect__option--active"));
    let ni = idx + dir;
    if (ni < 0) ni = options.length - 1;
    if (ni >= options.length) ni = 0;
    options.forEach(o => o.classList.remove("cselect__option--active"));
    const next = options[ni];
    next.classList.add("cselect__option--active");
    next.scrollIntoView({ block: "nearest" });
  };

  list.addEventListener("keydown", (e) => {
    if (e.key === "Escape") { setOpen(false); btn.focus(); }
    else if (e.key === "ArrowDown") { e.preventDefault(); move(1); }
    else if (e.key === "ArrowUp") { e.preventDefault(); move(-1); }
    else if (e.key === "Enter") {
      e.preventDefault();
      const cur = options.find(o => o.classList.contains("cselect__option--active")) || options[0];
      commit(cur);
    }
  });

  // click-away
  document.addEventListener("click", (e) => {
    if (!root.contains(e.target)) setOpen(false);
  });
}

// init after DOMContentLoaded
document.addEventListener("DOMContentLoaded", () => {
  enhanceCustomSelect("cselect-role");
});
