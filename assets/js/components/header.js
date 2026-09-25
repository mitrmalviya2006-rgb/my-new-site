// M'CHASHMA Eyewear - Header, Navigation & Search Component

import { productsData } from "../data/products.js";
import { Storage } from "../utils/storage.js";

export function initHeader() {
  const header = document.querySelector(".site-header");
  const themeToggleBtn = document.getElementById("theme-toggle-btn");
  const cartToggleBtn = document.getElementById("cart-toggle-btn");
  const cartBadge = document.getElementById("cart-count-badge");
  const searchInput = document.getElementById("header-search-input");
  const searchClearBtn = document.getElementById("search-clear-btn");
  const searchDropdown = document.getElementById("search-dropdown");
  const mobileNavToggle = document.getElementById("mobile-nav-toggle");
  const mobileNavDrawer = document.getElementById("mobile-nav-drawer");
  const promoBanner = document.getElementById("promo-banner");
  const promoCloseBtn = document.getElementById("promo-close-btn");

  // Initial Theme Setup
  const currentTheme = Storage.getTheme();
  document.documentElement.setAttribute("data-theme", currentTheme);
  updateThemeIcon(currentTheme);

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener("click", () => {
      const nextTheme = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
      Storage.setTheme(nextTheme);
      updateThemeIcon(nextTheme);
    });
  }

  function updateThemeIcon(theme) {
    if (!themeToggleBtn) return;
    if (theme === "dark") {
      themeToggleBtn.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="5"></circle>
          <line x1="12" y1="1" x2="12" y2="3"></line>
          <line x1="12" y1="21" x2="12" y2="23"></line>
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
          <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
          <line x1="1" y1="12" x2="3" y2="12"></line>
          <line x1="21" y1="12" x2="23" y2="12"></line>
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
          <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
        </svg>
      `;
      themeToggleBtn.title = "Switch to Light Mode";
    } else {
      themeToggleBtn.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
        </svg>
      `;
      themeToggleBtn.title = "Switch to Dark Mode";
    }
  }

  // Sticky Header Scroll Detection
  window.addEventListener("scroll", () => {
    if (window.scrollY > 20) {
      header?.classList.add("scrolled");
    } else {
      header?.classList.remove("scrolled");
    }
  });

  // Cart Badge Update
  function updateBadge() {
    if (!cartBadge) return;
    const count = Storage.getCartCount();
    cartBadge.textContent = count;
    cartBadge.style.display = count > 0 ? "flex" : "none";
  }
  updateBadge();
  window.addEventListener("cart-updated", updateBadge);

  // Search Live Autocomplete
  if (searchInput && searchDropdown) {
    searchInput.addEventListener("input", (e) => {
      const query = e.target.value.trim().toLowerCase();
      if (searchClearBtn) {
        searchClearBtn.classList.toggle("active", query.length > 0);
      }

      if (query.length < 2) {
        searchDropdown.classList.remove("active");
        searchDropdown.innerHTML = "";
        return;
      }

      const matches = productsData.filter(p =>
        p.name.toLowerCase().includes(query) ||
        p.category.toLowerCase().includes(query) ||
        p.shape.toLowerCase().includes(query) ||
        p.colorName.toLowerCase().includes(query)
      ).slice(0, 5);

      if (matches.length === 0) {
        searchDropdown.innerHTML = `<div style="padding: 12px; font-size: 0.88rem; color: var(--text-muted); text-align: center;">No matching frames found for "${query}"</div>`;
      } else {
        searchDropdown.innerHTML = `
          <div style="font-size: 0.76rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted); margin-bottom: 8px; padding-left: 6px;">Matching Products</div>
          ${matches.map(p => `
            <div class="search-result-item" data-product-id="${p.id}" style="display: flex; align-items: center; gap: 12px; padding: 8px; border-radius: 8px; cursor: pointer; transition: background 0.2s;">
              <img src="${p.image}" alt="${p.name}" style="width: 48px; height: 36px; object-fit: contain; background: var(--bg-tertiary); border-radius: 6px; padding: 2px;">
              <div style="flex: 1; min-width: 0;">
                <div style="font-size: 0.88rem; font-weight: 700; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${p.name}</div>
                <div style="font-size: 0.78rem; color: var(--text-muted);">${p.shape.toUpperCase()} • ₹${p.salePrice.toLocaleString('en-IN')}</div>
              </div>
            </div>
          `).join('')}
        `;

        // Click on search result item
        searchDropdown.querySelectorAll(".search-result-item").forEach(item => {
          item.addEventListener("click", () => {
            const pid = item.getAttribute("data-product-id");
            window.dispatchEvent(new CustomEvent("open-product-modal", { detail: { productId: pid } }));
            searchDropdown.classList.remove("active");
            searchInput.value = "";
          });
        });
      }

      searchDropdown.classList.add("active");
    });

    if (searchClearBtn) {
      searchClearBtn.addEventListener("click", () => {
        searchInput.value = "";
        searchClearBtn.classList.remove("active");
        searchDropdown.classList.remove("active");
      });
    }

    document.addEventListener("click", (e) => {
      if (!searchInput.contains(e.target) && !searchDropdown.contains(e.target)) {
        searchDropdown.classList.remove("active");
      }
    });
  }

  // Promo Banner Close
  if (promoCloseBtn && promoBanner) {
    promoCloseBtn.addEventListener("click", () => {
      promoBanner.style.display = "none";
    });
  }

  // Mobile Nav Drawer Toggle
  if (mobileNavToggle && mobileNavDrawer) {
    mobileNavToggle.addEventListener("click", () => {
      mobileNavDrawer.classList.toggle("active");
    });
  }
}
