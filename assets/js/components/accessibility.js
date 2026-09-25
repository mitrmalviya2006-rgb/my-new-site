// M'CHASHMA Eyewear - Universal Accessibility (WCAG 2.1) Controller

import { I18n } from "../utils/i18n.js";

const A11Y_STORAGE_KEY = "mchashma_a11y_prefs";

export function initAccessibility() {
  const launcherBtn = document.getElementById("a11y-launcher-btn");
  const modal = document.getElementById("a11y-modal");
  const closeBtn = document.getElementById("a11y-modal-close-btn");
  const liveRegion = document.getElementById("a11y-live-region");
  const readingGuideLine = document.getElementById("reading-guide-line");

  // Load Preferences
  const prefs = loadPreferences();
  applyPreferences(prefs);

  // Initialize Language
  I18n.applyTranslations();

  // Launcher Toggle
  function toggleModal() {
    modal?.classList.toggle("active");
    if (modal?.classList.contains("active")) {
      document.body.style.overflow = "hidden";
      announce("Accessibility options opened. Press Tab to browse options or Escape to close.");
    } else {
      document.body.style.overflow = "";
    }
  }

  launcherBtn?.addEventListener("click", toggleModal);
  closeBtn?.addEventListener("click", toggleModal);
  modal?.addEventListener("click", (e) => {
    if (e.target === modal) toggleModal();
  });

  // Global Keyboard Shortcuts
  window.addEventListener("keydown", (e) => {
    // Alt + A: Open Accessibility Panel
    if (e.altKey && (e.key === "a" || e.key === "A")) {
      e.preventDefault();
      toggleModal();
    }

    // Escape: Close any open modal or drawer
    if (e.key === "Escape") {
      document.querySelectorAll(".modal-backdrop.active, .drawer-panel.active").forEach(el => {
        el.classList.remove("active");
      });
      document.getElementById("cart-backdrop")?.classList.remove("active");
      document.body.style.overflow = "";
      announce("Closed dialog window.");
    }
  });

  // Font Size Buttons
  document.querySelectorAll("[data-a11y-font]").forEach(btn => {
    btn.addEventListener("click", () => {
      const size = btn.getAttribute("data-a11y-font");
      prefs.fontSize = size;
      applyPreferences(prefs);
      announce(`Font size changed to ${size || 'default'}.`);
    });
  });

  // Contrast Buttons
  document.querySelectorAll("[data-a11y-contrast]").forEach(btn => {
    btn.addEventListener("click", () => {
      const mode = btn.getAttribute("data-a11y-contrast");
      prefs.contrast = mode;
      applyPreferences(prefs);
      announce(`Contrast mode changed to ${mode || 'standard'}.`);
    });
  });

  // Dyslexia Mode Toggle
  document.getElementById("a11y-toggle-dyslexia")?.addEventListener("click", () => {
    prefs.dyslexia = !prefs.dyslexia;
    applyPreferences(prefs);
    announce(prefs.dyslexia ? "Dyslexia-friendly font enabled." : "Dyslexia-friendly font disabled.");
  });

  // Text Spacing Toggle
  document.getElementById("a11y-toggle-spacing")?.addEventListener("click", () => {
    prefs.textSpacing = !prefs.textSpacing;
    applyPreferences(prefs);
    announce(prefs.textSpacing ? "Enhanced text spacing enabled." : "Enhanced text spacing disabled.");
  });

  // Big Cursor Toggle
  document.getElementById("a11y-toggle-cursor")?.addEventListener("click", () => {
    prefs.bigCursor = !prefs.bigCursor;
    applyPreferences(prefs);
    announce(prefs.bigCursor ? "High-visibility large cursor enabled." : "Large cursor disabled.");
  });

  // Reading Guide Line Toggle
  document.getElementById("a11y-toggle-guide")?.addEventListener("click", () => {
    prefs.readingGuide = !prefs.readingGuide;
    applyPreferences(prefs);
    announce(prefs.readingGuide ? "Reading guide highlight bar enabled." : "Reading guide disabled.");
  });

  // Pause Animations Toggle
  document.getElementById("a11y-toggle-animations")?.addEventListener("click", () => {
    prefs.pauseAnimations = !prefs.pauseAnimations;
    applyPreferences(prefs);
    announce(prefs.pauseAnimations ? "All animations paused." : "Animations resumed.");
  });

  // Reset All Button
  document.getElementById("a11y-reset-all-btn")?.addEventListener("click", () => {
    const defaultPrefs = {
      fontSize: "normal",
      contrast: "normal",
      dyslexia: false,
      textSpacing: false,
      bigCursor: false,
      readingGuide: false,
      pauseAnimations: false
    };
    applyPreferences(defaultPrefs);
    announce("All accessibility settings reset to default.");
  });

  // Language Switcher Buttons (English & Hindi)
  document.querySelectorAll(".lang-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const lang = btn.getAttribute("data-lang");
      I18n.setLanguage(lang);
      announce(lang === "hi" ? "भाषा बदलकर हिन्दी कर दी गई है।" : "Language changed to English.");
    });
  });

  // Reading Guide Mouse Movement
  window.addEventListener("mousemove", (e) => {
    if (readingGuideLine && prefs.readingGuide) {
      readingGuideLine.style.top = `${e.clientY}px`;
    }
  });

  function loadPreferences() {
    try {
      const saved = localStorage.getItem(A11Y_STORAGE_KEY);
      return saved ? JSON.parse(saved) : {
        fontSize: "normal",
        contrast: "normal",
        dyslexia: false,
        textSpacing: false,
        bigCursor: false,
        readingGuide: false,
        pauseAnimations: false
      };
    } catch {
      return {};
    }
  }

  function applyPreferences(p) {
    const root = document.documentElement;

    // Font size
    if (p.fontSize && p.fontSize !== "normal") {
      root.setAttribute("data-font-size", p.fontSize);
    } else {
      root.removeAttribute("data-font-size");
    }

    // Contrast
    if (p.contrast && p.contrast !== "normal") {
      root.setAttribute("data-contrast", p.contrast);
    } else {
      root.removeAttribute("data-contrast");
    }

    // Dyslexia
    if (p.dyslexia) {
      root.setAttribute("data-dyslexia", "true");
    } else {
      root.removeAttribute("data-dyslexia");
    }

    // Text Spacing
    if (p.textSpacing) {
      root.setAttribute("data-text-spacing", "true");
    } else {
      root.removeAttribute("data-text-spacing");
    }

    // Big Cursor
    if (p.bigCursor) {
      root.setAttribute("data-big-cursor", "true");
    } else {
      root.removeAttribute("data-big-cursor");
    }

    // Reading Guide
    if (readingGuideLine) {
      readingGuideLine.classList.toggle("active", Boolean(p.readingGuide));
    }

    // Pause Animations
    if (p.pauseAnimations) {
      root.style.setProperty("--transition-normal", "0s");
      root.style.setProperty("--transition-spring", "0s");
      document.body.classList.add("paused-animations");
    } else {
      root.style.removeProperty("--transition-normal");
      root.style.removeProperty("--transition-spring");
      document.body.classList.remove("paused-animations");
    }

    // Sync button UI states
    syncButtons(p);

    // Save
    try {
      localStorage.setItem(A11Y_STORAGE_KEY, JSON.stringify(p));
    } catch (e) {
      console.warn("Could not save a11y preferences:", e);
    }
  }

  function syncButtons(p) {
    document.querySelectorAll("[data-a11y-font]").forEach(btn => {
      btn.classList.toggle("active", btn.getAttribute("data-a11y-font") === p.fontSize);
    });
    document.querySelectorAll("[data-a11y-contrast]").forEach(btn => {
      btn.classList.toggle("active", btn.getAttribute("data-a11y-contrast") === p.contrast);
    });
    document.getElementById("a11y-toggle-dyslexia")?.classList.toggle("active", Boolean(p.dyslexia));
    document.getElementById("a11y-toggle-spacing")?.classList.toggle("active", Boolean(p.textSpacing));
    document.getElementById("a11y-toggle-cursor")?.classList.toggle("active", Boolean(p.bigCursor));
    document.getElementById("a11y-toggle-guide")?.classList.toggle("active", Boolean(p.readingGuide));
    document.getElementById("a11y-toggle-animations")?.classList.toggle("active", Boolean(p.pauseAnimations));
  }

  function announce(text) {
    if (liveRegion) {
      liveRegion.textContent = text;
    }
  }
}
