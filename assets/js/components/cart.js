// M'CHASHMA Eyewear - Cart Drawer & Multi-Step Checkout Component

import { Storage } from "../utils/storage.js";

export function initCart() {
  const cartDrawer = document.getElementById("cart-drawer");
  const cartBackdrop = document.getElementById("cart-backdrop");
  const cartCloseBtn = document.getElementById("cart-close-btn");
  const cartItemsContainer = document.getElementById("cart-items-container");
  const cartSubtotalEl = document.getElementById("cart-subtotal-val");
  const cartDiscountEl = document.getElementById("cart-discount-val");
  const cartShippingEl = document.getElementById("cart-shipping-val");
  const cartTotalEl = document.getElementById("cart-total-val");
  const cartShippingProgressBar = document.getElementById("cart-shipping-progress");
  const cartShippingText = document.getElementById("cart-shipping-text");
  const promoInput = document.getElementById("cart-promo-input");
  const promoApplyBtn = document.getElementById("cart-promo-apply-btn");
  const promoMessageEl = document.getElementById("cart-promo-message");
  const checkoutBtn = document.getElementById("cart-checkout-btn");

  // Checkout Modal Elements
  const checkoutModal = document.getElementById("checkout-modal");
  const checkoutCloseBtn = document.getElementById("checkout-close-btn");
  const checkoutForm = document.getElementById("checkout-form");
  const orderConfirmModal = document.getElementById("order-confirmation-modal");
  const orderConfirmCloseBtn = document.getElementById("order-confirm-close-btn");

  // Open & Close Cart
  function openCart() {
    renderCart();
    cartBackdrop?.classList.add("active");
    cartDrawer?.classList.add("active");
    document.body.style.overflow = "hidden";
  }

  function closeCart() {
    cartBackdrop?.classList.remove("active");
    cartDrawer?.classList.remove("active");
    document.body.style.overflow = "";
  }

  document.getElementById("cart-toggle-btn")?.addEventListener("click", openCart);
  document.getElementById("cart-count-badge")?.addEventListener("click", openCart);
  window.addEventListener("open-cart-drawer", openCart);

  cartCloseBtn?.addEventListener("click", closeCart);
  cartBackdrop?.addEventListener("click", closeCart);

  // Re-render when cart updates
  window.addEventListener("cart-updated", renderCart);
  window.addEventListener("coupon-applied", renderCart);

  // Promo Code Handler
  if (promoApplyBtn && promoInput) {
    promoApplyBtn.addEventListener("click", () => {
      const code = promoInput.value.trim().toUpperCase();
      if (!code) return;

      if (code === "MCHASHMA50") {
        Storage.setCoupon("MCHASHMA50");
        if (promoMessageEl) {
          promoMessageEl.style.display = "block";
          promoMessageEl.style.color = "#10B981";
          promoMessageEl.textContent = "Coupon MCHASHMA50 applied! 50% discount on sunglasses.";
        }
      } else {
        if (promoMessageEl) {
          promoMessageEl.style.display = "block";
          promoMessageEl.style.color = "var(--brand-red)";
          promoMessageEl.textContent = "Invalid coupon code. Try 'MCHASHMA50' for 50% off sunglasses!";
        }
      }
    });
  }

  function renderCart() {
    if (!cartItemsContainer) return;
    const cart = Storage.getCart();
    const totals = Storage.calculateCartTotals();

    // Free shipping threshold (₹999)
    if (cartShippingProgressBar && cartShippingText) {
      const needed = Math.max(0, 999 - totals.subtotal);
      if (needed === 0) {
        cartShippingProgressBar.style.width = "100%";
        cartShippingProgressBar.style.background = "#10B981";
        cartShippingText.innerHTML = "🎉 Congratulations! You have unlocked <strong>FREE Express Shipping</strong>!";
      } else {
        const pct = Math.min(100, Math.round((totals.subtotal / 999) * 100));
        cartShippingProgressBar.style.width = `${pct}%`;
        cartShippingProgressBar.style.background = "var(--brand-yellow)";
        cartShippingText.innerHTML = `Add <strong>₹${needed.toLocaleString('en-IN')}</strong> more for <strong>FREE Delivery</strong>`;
      }
    }

    if (cart.length === 0) {
      cartItemsContainer.innerHTML = `
        <div style="text-align: center; padding: 60px 20px;">
          <div style="font-size: 3rem; margin-bottom: 12px; opacity: 0.6;">🛍️</div>
          <h4 style="font-family: var(--font-heading); font-size: 1.2rem; margin-bottom: 8px;">Your Shopping Cart is Empty</h4>
          <p style="font-size: 0.88rem; color: var(--text-muted); margin-bottom: 24px;">Browse our handcrafted eyeglasses and sunglasses to find your fit.</p>
          <button id="cart-start-shopping-btn" class="btn btn-primary btn-sm">Explore Frames</button>
        </div>
      `;
      document.getElementById("cart-start-shopping-btn")?.addEventListener("click", () => {
        closeCart();
        document.getElementById("catalog")?.scrollIntoView({ behavior: "smooth" });
      });

      if (cartSubtotalEl) cartSubtotalEl.textContent = "₹0";
      if (cartDiscountEl) cartDiscountEl.textContent = "-₹0";
      if (cartShippingEl) cartShippingEl.textContent = "₹0";
      if (cartTotalEl) cartTotalEl.textContent = "₹0";
      if (checkoutBtn) checkoutBtn.disabled = true;
      return;
    }

    if (checkoutBtn) checkoutBtn.disabled = false;

    // Render items
    cartItemsContainer.innerHTML = cart.map(item => {
      const lensName = item.selectedLens ? item.selectedLens.name : "Frame Only";
      const lensPrice = item.selectedLens ? item.selectedLens.price : 0;
      const unitTotal = item.price + lensPrice;
      const itemSubtotal = unitTotal * item.quantity;
      const lensId = item.selectedLens?.id || "none";

      return `
        <div class="cart-item-card" style="display: flex; gap: 14px; padding: 14px 0; border-bottom: 1px solid var(--border-subtle); align-items: center;">
          <img src="${item.image}" alt="${item.name}" style="width: 70px; height: 50px; object-fit: contain; background: var(--bg-secondary); border-radius: 8px; padding: 4px;">
          <div style="flex: 1; min-width: 0;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
              <h5 style="font-size: 0.92rem; font-weight: 700; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 2px;">${item.name}</h5>
              <button class="cart-remove-item-btn" data-remove-id="${item.id}" data-lens-id="${lensId}" style="color: var(--text-muted); font-size: 1.1rem; line-height: 1; padding: 2px 6px;">×</button>
            </div>
            <div style="font-size: 0.78rem; color: var(--text-muted); margin-bottom: 6px;">${lensName} • ${item.colorName || ''}</div>
            
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <div style="display: flex; align-items: center; border: 1px solid var(--border-strong); border-radius: 6px; overflow: hidden;">
                <button class="cart-qty-btn" data-action="minus" data-id="${item.id}" data-lens-id="${lensId}" style="width: 26px; height: 26px; background: var(--bg-secondary); font-weight: 700;">-</button>
                <span style="width: 32px; text-align: center; font-size: 0.85rem; font-weight: 700;">${item.quantity}</span>
                <button class="cart-qty-btn" data-action="plus" data-id="${item.id}" data-lens-id="${lensId}" style="width: 26px; height: 26px; background: var(--bg-secondary); font-weight: 700;">+</button>
              </div>
              <div style="font-size: 0.95rem; font-weight: 800; color: var(--text-primary);">
                ₹${itemSubtotal.toLocaleString('en-IN')}
              </div>
            </div>
          </div>
        </div>
      `;
    }).join('');

    // Attach item buttons
    cartItemsContainer.querySelectorAll(".cart-remove-item-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-remove-id");
        const lensId = btn.getAttribute("data-lens-id");
        Storage.removeFromCart(id, lensId);
      });
    });

    cartItemsContainer.querySelectorAll(".cart-qty-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const action = btn.getAttribute("data-action");
        const id = btn.getAttribute("data-id");
        const lensId = btn.getAttribute("data-lens-id");
        const currentItem = cart.find(i => i.id === id && (i.selectedLens?.id || "none") === lensId);
        if (currentItem) {
          const newQty = action === "plus" ? currentItem.quantity + 1 : currentItem.quantity - 1;
          Storage.updateCartQuantity(id, lensId, newQty);
        }
      });
    });

    // Totals
    if (cartSubtotalEl) cartSubtotalEl.textContent = `₹${totals.subtotal.toLocaleString('en-IN')}`;
    if (cartDiscountEl) cartDiscountEl.textContent = `-₹${totals.discount.toLocaleString('en-IN')}`;
    if (cartShippingEl) cartShippingEl.textContent = totals.shipping === 0 ? "FREE" : `₹${totals.shipping}`;
    if (cartTotalEl) cartTotalEl.textContent = `₹${totals.finalTotal.toLocaleString('en-IN')}`;
  }

  // Checkout Flow
  if (checkoutBtn) {
    checkoutBtn.addEventListener("click", () => {
      closeCart();
      openCheckoutModal();
    });
  }

  window.addEventListener("open-checkout-modal", openCheckoutModal);

  function openCheckoutModal() {
    const totals = Storage.calculateCartTotals();
    const summaryEl = document.getElementById("checkout-order-summary");
    if (summaryEl) {
      summaryEl.innerHTML = `
        <div style="background: var(--bg-secondary); border-radius: var(--radius-md); padding: 18px; margin-bottom: 20px;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 0.9rem;">
            <span>Items Subtotal:</span>
            <span>₹${totals.subtotal.toLocaleString('en-IN')}</span>
          </div>
          ${totals.discount > 0 ? `
            <div style="display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 0.9rem; color: #10B981;">
              <span>Promo Discount (MCHASHMA50):</span>
              <span>-₹${totals.discount.toLocaleString('en-IN')}</span>
            </div>
          ` : ''}
          <div style="display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 0.9rem;">
            <span>Express Shipping:</span>
            <span>${totals.shipping === 0 ? '<strong style="color: #10B981;">FREE</strong>' : '₹' + totals.shipping}</span>
          </div>
          <div style="display: flex; justify-content: space-between; font-size: 1.15rem; font-weight: 800; border-top: 1px solid var(--border-subtle); padding-top: 10px;">
            <span>Total Payable:</span>
            <span style="color: var(--brand-red);">₹${totals.finalTotal.toLocaleString('en-IN')}</span>
          </div>
        </div>
      `;
    }

    checkoutModal?.classList.add("active");
    document.body.style.overflow = "hidden";
  }

  function closeCheckoutModal() {
    checkoutModal?.classList.remove("active");
    document.body.style.overflow = "";
  }

  checkoutCloseBtn?.addEventListener("click", closeCheckoutModal);

  // Checkout Form Submission
  if (checkoutForm) {
    checkoutForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const name = document.getElementById("checkout-name")?.value.trim() || "Customer";
      const phone = document.getElementById("checkout-phone")?.value.trim() || "+91 98765 00000";
      const pin = document.getElementById("checkout-pincode")?.value.trim() || "110001";
      const city = document.getElementById("checkout-city")?.value.trim() || "Delhi";
      const paymentMethod = document.querySelector('input[name="payment-method"]:checked')?.value || "UPI";

      const orderId = "MC-IND-" + Math.floor(100000 + Math.random() * 900000);
      const totals = Storage.calculateCartTotals();

      closeCheckoutModal();
      Storage.clearCart();

      // Show Confirmation Modal
      showOrderConfirmation({
        orderId,
        name,
        phone,
        pin,
        city,
        paymentMethod,
        total: totals.finalTotal
      });
    });
  }

  function showOrderConfirmation(order) {
    const detailsContainer = document.getElementById("order-confirm-details");
    if (detailsContainer) {
      detailsContainer.innerHTML = `
        <div style="text-align: center; margin-bottom: 24px;">
          <div style="width: 72px; height: 72px; border-radius: 50%; background: #10B981; color: #FFFFFF; font-size: 2.2rem; display: flex; align-items: center; justify-content: center; margin: 0 auto 16px; box-shadow: 0 0 25px rgba(16, 185, 129, 0.4);">
            ✓
          </div>
          <h3 style="font-family: var(--font-heading); font-size: 1.6rem; font-weight: 800; margin-bottom: 6px;">Order Confirmed!</h3>
          <p style="font-size: 0.9rem; color: var(--text-muted);">Thank you for trusting M'CHASHMA Eyewear.</p>
        </div>

        <div style="background: var(--bg-secondary); border-radius: var(--radius-lg); padding: 22px; border: 1px solid var(--border-subtle); margin-bottom: 24px;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 0.92rem;">
            <span>Order Reference:</span>
            <strong style="font-family: monospace; color: var(--brand-red); font-size: 1rem;">${order.orderId}</strong>
          </div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 0.92rem;">
            <span>Recipient:</span>
            <strong>${order.name} (${order.phone})</strong>
          </div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 0.92rem;">
            <span>Shipping Destination:</span>
            <strong>${order.city}, PIN ${order.pin}</strong>
          </div>
          <div style="display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 0.92rem;">
            <span>Payment Mode:</span>
            <strong>${order.paymentMethod}</strong>
          </div>
          <div style="display: flex; justify-content: space-between; font-size: 1.1rem; font-weight: 800; border-top: 1px solid var(--border-subtle); padding-top: 12px; margin-top: 6px;">
            <span>Total Paid:</span>
            <span style="color: var(--brand-red);">₹${order.total.toLocaleString('en-IN')}</span>
          </div>
        </div>

        <div style="background: var(--brand-yellow-light); border: 1px solid var(--brand-yellow); border-radius: var(--radius-md); padding: 14px 18px; font-size: 0.85rem; color: #92400E; margin-bottom: 24px;">
          🚚 <strong>Next Steps:</strong> Your prescription is being reviewed by our Zeiss-certified optometrists. Express dispatch will occur within 24 hours with SMS live tracking!
        </div>

        <div style="display: flex; gap: 12px;">
          <button id="order-confirm-done-btn" class="btn btn-primary" style="flex: 1;">Continue Shopping</button>
        </div>
      `;

      document.getElementById("order-confirm-done-btn")?.addEventListener("click", () => {
        orderConfirmModal?.classList.remove("active");
        document.body.style.overflow = "";
      });
    }

    orderConfirmModal?.classList.add("active");
    document.body.style.overflow = "hidden";
  }

  orderConfirmCloseBtn?.addEventListener("click", () => {
    orderConfirmModal?.classList.remove("active");
    document.body.style.overflow = "";
  });
}
