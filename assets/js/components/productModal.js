// M'CHASHMA Eyewear - Product Detail Modal Component

import { productsData, lensPackages } from "../data/products.js";
import { Storage } from "../utils/storage.js";

export function initProductModal() {
  const modalBackdrop = document.getElementById("product-detail-modal");
  const modalContainer = document.getElementById("product-modal-content");
  const closeBtn = document.getElementById("modal-detail-close-btn");

  if (!modalBackdrop || !modalContainer) return;

  window.addEventListener("open-product-modal", (e) => {
    const productId = e.detail.productId;
    const product = productsData.find(p => p.id === productId);
    if (!product) return;
    renderDetail(product);
    modalBackdrop.classList.add("active");
    document.body.style.overflow = "hidden";
  });

  function closeModal() {
    modalBackdrop.classList.remove("active");
    document.body.style.overflow = "";
  }

  if (closeBtn) closeBtn.addEventListener("click", closeModal);
  modalBackdrop.addEventListener("click", (e) => {
    if (e.target === modalBackdrop) closeModal();
  });

  function renderDetail(product) {
    let selectedLens = lensPackages[0];
    let selectedPrescriptionType = "single-vision";

    modalContainer.innerHTML = `
      <div class="product-detail-grid">
        <!-- Left: Image Gallery -->
        <div class="product-detail-gallery">
          <div class="gallery-main-view">
            <img id="detail-active-img" src="${product.image}" alt="${product.name}" class="gallery-main-img">
          </div>
          <div class="gallery-thumbnails">
            ${product.gallery.map((imgSrc, idx) => `
              <button class="gallery-thumb-btn ${idx === 0 ? 'active' : ''}" data-thumb-src="${imgSrc}">
                <img src="${imgSrc}" alt="${product.name} view ${idx+1}" style="width: 100%; height: 100%; object-fit: contain;">
              </button>
            `).join('')}
          </div>

          <!-- Virtual Try-On Direct CTA -->
          <div style="background: var(--brand-yellow-light); border-radius: var(--radius-md); padding: 14px 18px; display: flex; align-items: center; justify-content: space-between; border: 1px solid var(--brand-yellow);">
            <div>
              <div style="font-size: 0.85rem; font-weight: 700; color: #92400E;">Want to see how it looks on you?</div>
              <div style="font-size: 0.78rem; color: #B45309;">Use your webcam or face photo instantly</div>
            </div>
            <button id="modal-tryon-btn" class="btn btn-yellow btn-sm">Try On</button>
          </div>

          <!-- Dimensions & Fitting Details -->
          <div class="detail-dimensions-card">
            <div class="dimensions-title">Frame Fitting & Size (Medium Fit)</div>
            <div class="dimensions-metrics">
              <div><strong>Lens:</strong> ${product.dimensions.lensWidth} mm</div>
              <div><strong>Bridge:</strong> ${product.dimensions.bridgeWidth} mm</div>
              <div><strong>Temple:</strong> ${product.dimensions.templeLength} mm</div>
              <div><strong>Weight:</strong> ${product.dimensions.weight}</div>
            </div>
          </div>
        </div>

        <!-- Right: Information, Lenses, Prescription -->
        <div class="product-detail-info">
          <div class="detail-badge-row">
            <span class="badge ${product.is50Off ? 'badge-sale' : 'badge-yellow'}">${product.badge}</span>
            <span class="badge badge-charcoal">${product.material.toUpperCase()}</span>
          </div>

          <h2 class="detail-title">${product.name}</h2>
          <div style="font-size: 0.9rem; color: var(--text-secondary); margin-bottom: 12px;">Color: <strong>${product.colorName}</strong></div>

          <div class="detail-price-box">
            <div class="detail-current-price" id="modal-computed-price">₹${product.salePrice.toLocaleString('en-IN')}</div>
            ${product.regularPrice > product.salePrice ? `<div style="font-size: 1.1rem; color: var(--text-muted); text-decoration: line-through;">₹${product.regularPrice.toLocaleString('en-IN')}</div>` : ''}
            <span class="detail-tax-note">(Inclusive of all GST taxes & hard case)</span>
          </div>

          <p style="font-size: 0.92rem; color: var(--text-secondary); line-height: 1.6; margin-bottom: 22px;">${product.description}</p>

          <!-- Prescription Options -->
          <div style="margin-bottom: 20px;">
            <label class="form-label">1. Choose Prescription Need</label>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 6px;">
              <button class="btn btn-glass btn-sm rx-type-btn active" data-rx="single-vision">Single Vision</button>
              <button class="btn btn-glass btn-sm rx-type-btn" data-rx="progressive">Progressive</button>
              <button class="btn btn-glass btn-sm rx-type-btn" data-rx="zero-power">Zero Power</button>
            </div>
          </div>

          <!-- Lens Packages Selection -->
          <div class="lens-packages-selector">
            <label class="form-label">2. Select Optical Lens Package</label>
            <div style="margin-top: 8px;">
              ${lensPackages.map((pkg, idx) => `
                <div class="lens-package-card ${idx === 0 ? 'selected' : ''}" data-lens-id="${pkg.id}">
                  <div>
                    <div style="font-weight: 700; font-size: 0.92rem; color: var(--text-primary); display: flex; align-items: center; gap: 8px;">
                      ${pkg.name}
                      ${pkg.badge ? `<span class="badge badge-yellow" style="font-size: 0.68rem; padding: 2px 6px;">${pkg.badge}</span>` : ''}
                    </div>
                    <div style="font-size: 0.78rem; color: var(--text-muted); margin-top: 2px;">${pkg.features.join(" • ")}</div>
                  </div>
                  <div style="font-weight: 800; font-size: 0.95rem; color: var(--brand-red);">
                    ${pkg.price === 0 ? 'FREE' : '+₹' + pkg.price.toLocaleString('en-IN')}
                  </div>
                </div>
              `).join('')}
            </div>
          </div>

          <!-- Pincode Delivery Estimate -->
          <div style="margin-bottom: 22px;">
            <label class="form-label">Check Delivery to Your Pincode</label>
            <div class="pincode-checker">
              <input type="text" id="modal-pincode-input" class="pincode-input" placeholder="Enter 6-digit Pincode (e.g. 110001)" maxlength="6">
              <button id="modal-pincode-btn" class="btn btn-charcoal btn-sm">Check</button>
            </div>
            <div id="modal-pincode-msg" class="pincode-result"></div>
          </div>

          <!-- CTA Buttons -->
          <div style="display: flex; gap: 14px; margin-top: auto;">
            <button id="modal-add-cart-btn" class="btn btn-primary" style="flex: 1;">
              Add to Cart
            </button>
            <button id="modal-buy-now-btn" class="btn btn-yellow" style="flex: 1;">
              Buy Now
            </button>
          </div>
        </div>
      </div>
    `;

    // Setup Gallery Switcher
    const activeImg = modalContainer.querySelector("#detail-active-img");
    modalContainer.querySelectorAll(".gallery-thumb-btn").forEach(thumb => {
      thumb.addEventListener("click", () => {
        modalContainer.querySelectorAll(".gallery-thumb-btn").forEach(t => t.classList.remove("active"));
        thumb.classList.add("active");
        if (activeImg) activeImg.src = thumb.getAttribute("data-thumb-src");
      });
    });

    // Setup Prescription Types
    modalContainer.querySelectorAll(".rx-type-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        modalContainer.querySelectorAll(".rx-type-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        selectedPrescriptionType = btn.getAttribute("data-rx");
      });
    });

    // Setup Lens Packages
    const computedPriceEl = modalContainer.querySelector("#modal-computed-price");
    modalContainer.querySelectorAll(".lens-package-card").forEach(card => {
      card.addEventListener("click", () => {
        modalContainer.querySelectorAll(".lens-package-card").forEach(c => c.classList.remove("selected"));
        card.classList.add("selected");
        const lensId = card.getAttribute("data-lens-id");
        selectedLens = lensPackages.find(l => l.id === lensId) || lensPackages[0];
        const totalPrice = product.salePrice + selectedLens.price;
        if (computedPriceEl) computedPriceEl.textContent = `₹${totalPrice.toLocaleString('en-IN')}`;
      });
    });

    // Pincode Checker
    const pincodeInput = modalContainer.querySelector("#modal-pincode-input");
    const pincodeBtn = modalContainer.querySelector("#modal-pincode-btn");
    const pincodeMsg = modalContainer.querySelector("#modal-pincode-msg");
    if (pincodeBtn && pincodeInput && pincodeMsg) {
      pincodeBtn.addEventListener("click", () => {
        const pin = pincodeInput.value.trim();
        if (/^\d{6}$/.test(pin)) {
          pincodeMsg.style.display = "block";
          pincodeMsg.innerHTML = `✓ Delivery available to <strong>${pin}</strong> within 48-72 hours. Cash on delivery & home trial eligible!`;
        } else {
          pincodeMsg.style.display = "block";
          pincodeMsg.style.color = "var(--brand-red)";
          pincodeMsg.textContent = "Please enter a valid 6-digit Indian PIN code.";
        }
      });
    }

    // Try On Button
    modalContainer.querySelector("#modal-tryon-btn")?.addEventListener("click", () => {
      closeModal();
      window.dispatchEvent(new CustomEvent("set-tryon-frame", {
        detail: { frameOverlay: product.frameOverlay, frameName: product.name }
      }));
      document.getElementById("tryon")?.scrollIntoView({ behavior: "smooth" });
    });

    // Add to Cart
    modalContainer.querySelector("#modal-add-cart-btn")?.addEventListener("click", () => {
      Storage.addToCart(product, selectedLens, { type: selectedPrescriptionType });
      closeModal();
      window.dispatchEvent(new CustomEvent("show-toast", {
        detail: { message: `Added "${product.name}" with ${selectedLens.name} to cart!`, type: "success" }
      }));
      window.dispatchEvent(new CustomEvent("open-cart-drawer"));
    });

    // Buy Now
    modalContainer.querySelector("#modal-buy-now-btn")?.addEventListener("click", () => {
      Storage.addToCart(product, selectedLens, { type: selectedPrescriptionType });
      closeModal();
      window.dispatchEvent(new CustomEvent("open-checkout-modal"));
    });
  }
}
