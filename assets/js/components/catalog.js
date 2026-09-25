// M'CHASHMA Eyewear - Shop Catalog & Live Filtering Component

import { productsData } from "../data/products.js";
import { Storage } from "../utils/storage.js";

export function initCatalog() {
  const gridContainer = document.getElementById("products-grid");
  const toolbarCount = document.getElementById("toolbar-count");
  const sortSelect = document.getElementById("catalog-sort-select");
  const priceSlider = document.getElementById("price-range-slider");
  const priceSliderVal = document.getElementById("price-slider-value");
  const resetFiltersBtn = document.getElementById("reset-filters-btn");

  if (!gridContainer) return;

  // Active Filter State
  const state = {
    category: "all",
    gender: "all",
    shapes: new Set(),
    materials: new Set(),
    colors: new Set(),
    maxPrice: 6000,
    prescriptionOnly: false,
    sortBy: "featured"
  };

  // Listen for category selection from Category cards or Nav links
  window.addEventListener("filter-category", (e) => {
    state.category = e.detail.category || "all";
    syncCategoryUI();
    render();
    scrollToCatalog();
  });

  function scrollToCatalog() {
    const catalogEl = document.getElementById("catalog");
    if (catalogEl) {
      catalogEl.scrollIntoView({ behavior: "smooth" });
    }
  }

  function syncCategoryUI() {
    document.querySelectorAll(".category-card").forEach(card => {
      const cat = card.getAttribute("data-category");
      card.classList.toggle("active", cat === state.category);
    });
    document.querySelectorAll(".nav-link[data-category]").forEach(link => {
      const cat = link.getAttribute("data-category");
      link.classList.toggle("active", cat === state.category);
    });
  }

  // Setup category cards click
  document.querySelectorAll(".category-card").forEach(card => {
    card.addEventListener("click", () => {
      const cat = card.getAttribute("data-category");
      state.category = cat === state.category ? "all" : cat;
      syncCategoryUI();
      render();
      scrollToCatalog();
    });
  });

  // Setup Sidebar Checkboxes
  document.querySelectorAll("input[data-filter-group]").forEach(input => {
    input.addEventListener("change", (e) => {
      const group = e.target.getAttribute("data-filter-group");
      const val = e.target.value;
      if (group === "shape") {
        e.target.checked ? state.shapes.add(val) : state.shapes.delete(val);
      } else if (group === "material") {
        e.target.checked ? state.materials.add(val) : state.materials.delete(val);
      } else if (group === "gender") {
        state.gender = e.target.checked ? val : "all";
      } else if (group === "rx") {
        state.prescriptionOnly = e.target.checked;
      }
      render();
    });
  });

  // Color Swatches in Filters
  document.querySelectorAll(".color-swatch-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const color = btn.getAttribute("data-color");
      if (state.colors.has(color)) {
        state.colors.delete(color);
        btn.classList.remove("active");
      } else {
        state.colors.add(color);
        btn.classList.add("active");
      }
      render();
    });
  });

  // Price Slider
  if (priceSlider && priceSliderVal) {
    priceSlider.addEventListener("input", (e) => {
      state.maxPrice = Number(e.target.value);
      priceSliderVal.textContent = `₹${state.maxPrice.toLocaleString('en-IN')}`;
      render();
    });
  }

  // Sort Selector
  if (sortSelect) {
    sortSelect.addEventListener("change", (e) => {
      state.sortBy = e.target.value;
      render();
    });
  }

  // Reset Filters
  if (resetFiltersBtn) {
    resetFiltersBtn.addEventListener("click", () => {
      state.category = "all";
      state.gender = "all";
      state.shapes.clear();
      state.materials.clear();
      state.colors.clear();
      state.maxPrice = 6000;
      state.prescriptionOnly = false;
      state.sortBy = "featured";

      document.querySelectorAll("input[data-filter-group]").forEach(inp => inp.checked = false);
      document.querySelectorAll(".color-swatch-btn").forEach(btn => btn.classList.remove("active"));
      if (priceSlider) priceSlider.value = 6000;
      if (priceSliderVal) priceSliderVal.textContent = "₹6,000";
      if (sortSelect) sortSelect.value = "featured";
      syncCategoryUI();
      render();
    });
  }

  function getFilteredProducts() {
    return productsData.filter(product => {
      if (state.category !== "all" && product.category !== state.category) return false;
      if (state.gender !== "all" && product.gender !== state.gender && product.gender !== "unisex") return false;
      if (state.shapes.size > 0 && !state.shapes.has(product.shape)) return false;
      if (state.materials.size > 0 && !state.materials.has(product.material)) return false;
      if (state.colors.size > 0 && !state.colors.has(product.color)) return false;
      if (product.salePrice > state.maxPrice) return false;
      if (state.prescriptionOnly && !product.prescriptionCompatible) return false;
      return true;
    }).sort((a, b) => {
      if (state.sortBy === "price-low") return a.salePrice - b.salePrice;
      if (state.sortBy === "price-high") return b.salePrice - a.salePrice;
      if (state.sortBy === "rating") return b.rating - a.rating;
      return 0; // default featured
    });
  }

  function render() {
    const filtered = getFilteredProducts();
    if (toolbarCount) {
      toolbarCount.textContent = `Showing ${filtered.length} of ${productsData.length} frames`;
    }

    if (filtered.length === 0) {
      gridContainer.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 60px 20px; background: var(--bg-card); border-radius: 20px; border: 1.5px dashed var(--border-strong);">
          <div style="font-size: 2.5rem; margin-bottom: 12px;">👓</div>
          <h3 style="font-family: var(--font-heading); font-size: 1.3rem; margin-bottom: 8px;">No frames match your exact filters</h3>
          <p style="color: var(--text-muted); font-size: 0.92rem; margin-bottom: 20px;">Try adjusting your price range, shape, or material selection.</p>
          <button id="clear-filters-empty-btn" class="btn btn-primary btn-sm">Clear All Filters</button>
        </div>
      `;
      document.getElementById("clear-filters-empty-btn")?.addEventListener("click", () => {
        resetFiltersBtn?.click();
      });
      return;
    }

    gridContainer.innerHTML = filtered.map(product => {
      const inWishlist = Storage.isInWishlist(product.id);
      return `
        <div class="product-card" data-product-id="${product.id}">
          <div class="product-card-top">
            <span class="badge ${product.is50Off ? 'badge-sale' : (product.badge === 'Zeiss Certified' ? 'badge-zeiss' : 'badge-yellow')}">${product.badge}</span>
            <button class="product-wishlist-btn ${inWishlist ? 'active' : ''}" data-wishlist-id="${product.id}" aria-label="Save to Wishlist" title="Save to Wishlist">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="${inWishlist ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>
              </svg>
            </button>
          </div>

          <div class="product-card-media" data-open-detail="${product.id}">
            <img src="${product.image}" alt="${product.name}" class="product-card-img" loading="lazy">
            <div class="product-quick-actions">
              <button class="btn btn-yellow btn-sm btn-quick-tryon" data-tryon-frame="${product.frameOverlay}" data-tryon-name="${product.name}" style="flex: 1;">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                  <circle cx="12" cy="13" r="4"></circle>
                </svg>
                Try On
              </button>
              <button class="btn btn-primary btn-sm btn-quick-add" data-add-id="${product.id}" style="flex: 1;">
                + Add
              </button>
            </div>
          </div>

          <div class="product-card-body">
            <div class="product-card-brand">M'CHASHMA • ${product.category.toUpperCase().replace('-', ' ')}</div>
            <h3 class="product-card-title" data-open-detail="${product.id}">${product.name}</h3>
            <div class="product-card-specs">${product.colorName} • ${product.material.toUpperCase()}</div>
            <div class="product-card-rating">
              <span>★</span>
              <span>${product.rating}</span>
              <span style="color: var(--text-muted); font-size: 0.78rem;">(${product.reviewsCount})</span>
            </div>

            <div class="product-card-bottom">
              <div class="product-card-price-group">
                <div class="product-current-price">₹${product.salePrice.toLocaleString('en-IN')}</div>
                ${product.regularPrice > product.salePrice ? `<div class="product-original-price">₹${product.regularPrice.toLocaleString('en-IN')}</div>` : ''}
              </div>
              <button class="btn btn-glass btn-sm" data-open-detail="${product.id}">
                Configure
              </button>
            </div>
          </div>
        </div>
      `;
    }).join('');

    // Attach Event Listeners to newly rendered cards
    attachCardEvents();
  }

  function attachCardEvents() {
    // Open detail modal
    gridContainer.querySelectorAll("[data-open-detail]").forEach(el => {
      el.addEventListener("click", () => {
        const pid = el.getAttribute("data-open-detail");
        window.dispatchEvent(new CustomEvent("open-product-modal", { detail: { productId: pid } }));
      });
    });

    // Quick Add to Cart
    gridContainer.querySelectorAll(".btn-quick-add").forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const pid = btn.getAttribute("data-add-id");
        const prod = productsData.find(p => p.id === pid);
        if (prod) {
          Storage.addToCart(prod);
          window.dispatchEvent(new CustomEvent("show-toast", {
            detail: { message: `Added "${prod.name}" to your cart!`, type: "success" }
          }));
        }
      });
    });

    // Quick Try On
    gridContainer.querySelectorAll(".btn-quick-tryon").forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const frameOverlay = btn.getAttribute("data-tryon-frame");
        const frameName = btn.getAttribute("data-tryon-name");
        window.dispatchEvent(new CustomEvent("set-tryon-frame", {
          detail: { frameOverlay, frameName }
        }));
        const tryonSection = document.getElementById("tryon");
        if (tryonSection) {
          tryonSection.scrollIntoView({ behavior: "smooth" });
        }
      });
    });

    // Wishlist Toggle
    gridContainer.querySelectorAll("[data-wishlist-id]").forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const pid = btn.getAttribute("data-wishlist-id");
        const active = Storage.toggleWishlist(pid);
        btn.classList.toggle("active", active);
        const svg = btn.querySelector("svg");
        if (svg) svg.setAttribute("fill", active ? "currentColor" : "none");
        window.dispatchEvent(new CustomEvent("show-toast", {
          detail: { message: active ? "Saved to your Wishlist!" : "Removed from Wishlist", type: "success" }
        }));
      });
    });
  }

  // Initial Render
  render();
}
