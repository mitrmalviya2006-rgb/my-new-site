// M'CHASHMA Eyewear - Local Persistence Manager (Cart, Wishlist, Theme)

const CART_KEY = "mchashma_cart_items";
const WISHLIST_KEY = "mchashma_wishlist";
const THEME_KEY = "mchashma_theme";
const COUPON_KEY = "mchashma_active_coupon";

export const Storage = {
  // Cart Operations
  getCart() {
    try {
      const data = localStorage.getItem(CART_KEY);
      return data ? JSON.parse(data) : [];
    } catch (e) {
      console.warn("Storage access failed, using memory:", e);
      return [];
    }
  },

  saveCart(items) {
    try {
      localStorage.setItem(CART_KEY, JSON.stringify(items));
      window.dispatchEvent(new CustomEvent("cart-updated", { detail: { items } }));
    } catch (e) {
      console.warn("Failed to persist cart:", e);
    }
  },

  addToCart(product, selectedLens = null, prescription = null, quantity = 1) {
    const cart = this.getCart();
    const lensId = selectedLens ? selectedLens.id : "none";
    const existingIndex = cart.findIndex(
      item => item.id === product.id && (item.selectedLens?.id || "none") === lensId
    );

    if (existingIndex > -1) {
      cart[existingIndex].quantity += quantity;
    } else {
      cart.push({
        id: product.id,
        name: product.name,
        category: product.category,
        image: product.image,
        colorName: product.colorName,
        price: product.salePrice,
        regularPrice: product.regularPrice,
        is50Off: product.is50Off,
        selectedLens,
        prescription,
        quantity
      });
    }
    this.saveCart(cart);
    return cart;
  },

  updateCartQuantity(id, lensId, newQuantity) {
    let cart = this.getCart();
    if (newQuantity <= 0) {
      cart = cart.filter(item => !(item.id === id && (item.selectedLens?.id || "none") === lensId));
    } else {
      const item = cart.find(item => item.id === id && (item.selectedLens?.id || "none") === lensId);
      if (item) item.quantity = newQuantity;
    }
    this.saveCart(cart);
    return cart;
  },

  removeFromCart(id, lensId) {
    return this.updateCartQuantity(id, lensId, 0);
  },

  clearCart() {
    this.saveCart([]);
  },

  getCartCount() {
    return this.getCart().reduce((sum, item) => sum + item.quantity, 0);
  },

  getCoupon() {
    return localStorage.getItem(COUPON_KEY) || "";
  },

  setCoupon(code) {
    localStorage.setItem(COUPON_KEY, code.toUpperCase());
    window.dispatchEvent(new CustomEvent("coupon-applied", { detail: { code } }));
  },

  removeCoupon() {
    localStorage.removeItem(COUPON_KEY);
    window.dispatchEvent(new CustomEvent("coupon-applied", { detail: { code: "" } }));
  },

  calculateCartTotals() {
    const cart = this.getCart();
    const coupon = this.getCoupon();
    let subtotal = 0;
    let sunglassesDiscount = 0;
    let couponDiscount = 0;

    cart.forEach(item => {
      const itemBasePrice = item.price;
      const lensPrice = item.selectedLens ? item.selectedLens.price : 0;
      const totalItemPrice = (itemBasePrice + lensPrice) * item.quantity;
      subtotal += totalItemPrice;

      // Check coupon MCHASHMA50 for sunglasses or 50% discount
      if (coupon === "MCHASHMA50" && item.category === "sunglasses") {
        sunglassesDiscount += (itemBasePrice * 0.5) * item.quantity;
      }
    });

    const isShippingFree = subtotal >= 999;
    const shipping = isShippingFree ? 0 : 99;
    const discount = sunglassesDiscount;
    const finalTotal = Math.max(0, subtotal - discount + shipping);

    return {
      subtotal,
      discount,
      shipping,
      isShippingFree,
      finalTotal,
      itemCount: this.getCartCount(),
      activeCoupon: coupon
    };
  },

  // Wishlist Operations
  getWishlist() {
    try {
      const data = localStorage.getItem(WISHLIST_KEY);
      return data ? JSON.parse(data) : [];
    } catch {
      return [];
    }
  },

  toggleWishlist(productId) {
    let wishlist = this.getWishlist();
    const index = wishlist.indexOf(productId);
    if (index > -1) {
      wishlist.splice(index, 1);
    } else {
      wishlist.push(productId);
    }
    localStorage.setItem(WISHLIST_KEY, JSON.stringify(wishlist));
    window.dispatchEvent(new CustomEvent("wishlist-updated", { detail: { wishlist } }));
    return wishlist.includes(productId);
  },

  isInWishlist(productId) {
    return this.getWishlist().includes(productId);
  },

  // Theme Operations
  getTheme() {
    return localStorage.getItem(THEME_KEY) || "light";
  },

  setTheme(theme) {
    localStorage.setItem(THEME_KEY, theme);
    document.documentElement.setAttribute("data-theme", theme);
    window.dispatchEvent(new CustomEvent("theme-changed", { detail: { theme } }));
  }
};
