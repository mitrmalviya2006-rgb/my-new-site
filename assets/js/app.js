// M'CHASHMA Eyewear - Main Application Entrypoint

import { initHeader } from "./components/header.js";
import { initCatalog } from "./components/catalog.js";
import { initProductModal } from "./components/productModal.js";
import { initCart } from "./components/cart.js";
import { initTryOn } from "./components/tryon.js";
import { initEyeCheck } from "./components/eyeCheck.js";
import { initAIGuide } from "./components/aiGuide.js";
import { initStoreSection } from "./components/storeSection.js";
import { initAccessibility } from "./components/accessibility.js";

document.addEventListener("DOMContentLoaded", () => {
  // 1. Universal Accessibility System
  initAccessibility();

  // 2. Scroll-Driven Intro Screen Animation (Slide 2 Requirement)
  handleIntroAnimation();

  // 2. Initialize Components
  initHeader();
  initCatalog();
  initProductModal();
  initCart();
  initTryOn();
  initEyeCheck();
  initAIGuide();
  initStoreSection();

  // 3. Scroll-Driven Product Storytelling Animations (IntersectionObserver)
  initScrollAnimations();

  // 4. Toast Notification System
  initToastSystem();

  // 5. Setup Navigation Links
  setupNavLinks();

  // 6. Newsletter Subscription
  setupNewsletter();
});

function handleIntroAnimation() {
  const introOverlay = document.getElementById("brand-intro-overlay");
  if (!introOverlay) return;

  // Check if reduced motion is requested
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const timeout = prefersReducedMotion ? 200 : 1500;

  setTimeout(() => {
    introOverlay.classList.add("fade-out");
    setTimeout(() => {
      introOverlay.style.display = "none";
    }, 800);
  }, timeout);
}

function initScrollAnimations() {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    document.querySelectorAll(".story-media-box, .story-text-block").forEach(el => {
      el.classList.add("in-view");
    });
    return;
  }

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add("in-view");
      }
    });
  }, {
    threshold: 0.2
  });

  document.querySelectorAll(".story-media-box, .story-text-block").forEach(el => {
    observer.observe(el);
  });
}

function initToastSystem() {
  const toastContainer = document.getElementById("toast-container");
  if (!toastContainer) return;

  window.addEventListener("show-toast", (e) => {
    const { message, type = "success" } = e.detail;
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <span style="font-size: 1.1rem;">${type === 'success' ? '✓' : (type === 'danger' ? '✕' : 'ℹ')}</span>
      <span>${message}</span>
    `;

    toastContainer.appendChild(toast);
    setTimeout(() => toast.classList.add("show"), 20);

    setTimeout(() => {
      toast.classList.remove("show");
      setTimeout(() => toast.remove(), 350);
    }, 4000);
  });
}

function setupNavLinks() {
  document.querySelectorAll("[data-nav-target]").forEach(link => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      const targetId = link.getAttribute("data-nav-target");
      const category = link.getAttribute("data-category");

      // Close mobile drawer if open
      document.getElementById("mobile-nav-drawer")?.classList.remove("active");

      if (category) {
        window.dispatchEvent(new CustomEvent("filter-category", { detail: { category } }));
      } else if (targetId) {
        const el = document.getElementById(targetId);
        if (el) {
          el.scrollIntoView({ behavior: "smooth" });
        }
      }
    });
  });
}

function setupNewsletter() {
  const form = document.getElementById("newsletter-form");
  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const input = document.getElementById("newsletter-email");
      if (input && input.value) {
        input.value = "";
        window.dispatchEvent(new CustomEvent("show-toast", {
          detail: {
            message: "Welcome to M'CHASHMA Privé! Your ₹500 welcome voucher code has been emailed.",
            type: "success"
          }
        }));
      }
    });
  }
}
