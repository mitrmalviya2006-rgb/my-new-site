// M'CHASHMA Eyewear - AI Shopping Assistant ("M'CHASHMA Guide")

import { productsData } from "../data/products.js";

export function initAIGuide() {
  const launcherBtn = document.getElementById("ai-launcher-btn");
  const chatWindow = document.getElementById("ai-chat-window");
  const closeBtn = document.getElementById("ai-chat-close-btn");
  const messagesContainer = document.getElementById("ai-messages-container");
  const chatInput = document.getElementById("ai-chat-input");
  const sendBtn = document.getElementById("ai-send-btn");
  const suggestionsContainer = document.getElementById("ai-suggestions-container");

  if (!launcherBtn || !chatWindow) return;

  // Initial Conversation Starters
  const initialSuggestions = [
    "What frames suit an Oval face?",
    "Best lenses for heavy computer screen work?",
    "Show me 50% off sunglasses",
    "How do 2-in-1 Convertibles work?",
    "Frames under ₹3,000"
  ];

  function toggleChat() {
    chatWindow.classList.toggle("active");
    if (chatWindow.classList.contains("active")) {
      chatInput?.focus();
    }
  }

  launcherBtn.addEventListener("click", toggleChat);
  closeBtn?.addEventListener("click", toggleChat);

  // Render initial suggestions
  function renderSuggestions(list) {
    if (!suggestionsContainer) return;
    suggestionsContainer.innerHTML = list.map(text => `
      <button class="suggestion-chip" data-query="${text}">${text}</button>
    `).join('');

    suggestionsContainer.querySelectorAll(".suggestion-chip").forEach(chip => {
      chip.addEventListener("click", () => {
        const query = chip.getAttribute("data-query");
        if (query) handleUserMessage(query);
      });
    });
  }
  renderSuggestions(initialSuggestions);

  // Send Message
  function handleSend() {
    const text = chatInput.value.trim();
    if (!text) return;
    chatInput.value = "";
    handleUserMessage(text);
  }

  sendBtn?.addEventListener("click", handleSend);
  chatInput?.addEventListener("keydown", (e) => {
    if (e.key === "Enter") handleSend();
  });

  function handleUserMessage(text) {
    appendMessage(text, "user");
    showTypingIndicator();

    setTimeout(() => {
      removeTypingIndicator();
      const response = generateAIResponse(text);
      appendMessage(response.text, "ai", response.recommendedProducts);

      if (response.newSuggestions) {
        renderSuggestions(response.newSuggestions);
      }
    }, 650);
  }

  function appendMessage(text, sender, products = []) {
    if (!messagesContainer) return;
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${sender === 'user' ? 'user-msg' : 'ai-msg'}`;

    let html = `<div style="font-size: 0.9rem;">${text}</div>`;

    if (products && products.length > 0) {
      html += `
        <div style="margin-top: 10px; display: flex; flex-direction: column; gap: 8px;">
          ${products.map(p => `
            <div class="chat-product-card" data-card-id="${p.id}">
              <img src="${p.image}" alt="${p.name}" class="chat-product-thumb">
              <div class="chat-product-info">
                <h5>${p.name}</h5>
                <div style="font-size: 0.74rem; color: var(--text-muted);">${p.colorName}</div>
                <div class="chat-product-price">₹${p.salePrice.toLocaleString('en-IN')} <span style="font-size: 0.72rem; color: var(--text-muted); text-decoration: line-through;">${p.regularPrice > p.salePrice ? '₹' + p.regularPrice.toLocaleString('en-IN') : ''}</span></div>
              </div>
            </div>
          `).join('')}
        </div>
      `;
    }

    bubble.innerHTML = html;
    messagesContainer.appendChild(bubble);

    // Attach click events on recommended products
    bubble.querySelectorAll(".chat-product-card").forEach(card => {
      card.addEventListener("click", () => {
        const pid = card.getAttribute("data-card-id");
        window.dispatchEvent(new CustomEvent("open-product-modal", { detail: { productId: pid } }));
      });
    });

    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  function showTypingIndicator() {
    const typing = document.createElement("div");
    typing.id = "ai-typing-indicator";
    typing.className = "chat-bubble ai-msg";
    typing.style.padding = "10px 16px";
    typing.innerHTML = `<span style="font-size: 0.8rem; color: var(--text-muted); display: inline-flex; align-items: center; gap: 4px;">Analyzing optical catalog <span>●</span><span>●</span><span>●</span></span>`;
    messagesContainer?.appendChild(typing);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  function removeTypingIndicator() {
    document.getElementById("ai-typing-indicator")?.remove();
  }

  // Local AI Response Engine
  function generateAIResponse(query) {
    const q = query.toLowerCase();

    // 1. Face Shape Inquiries
    if (q.includes("oval") || q.includes("face shape")) {
      const recs = productsData.filter(p => p.shape === "wayfarer" || p.shape === "hexagonal").slice(0, 2);
      return {
        text: "Oval face shapes are the most versatile! Balanced geometric frames, soft wayfarers, or modern octagons complement natural cheekbone proportions beautifully. Here are two bespoke styles you can try on right now:",
        recommendedProducts: recs,
        newSuggestions: ["Try Aviators", "Frames for Round face", "What about High Prescription?"]
      };
    }

    if (q.includes("round face")) {
      const recs = productsData.filter(p => p.shape === "rectangle" || p.shape === "wayfarer").slice(0, 2);
      return {
        text: "For round faces, structured rectangular or angular wayfarer frames add flattering definition and lengthen facial features. Here are top recommended choices:",
        recommendedProducts: recs,
        newSuggestions: ["Titanium frames", "Check 50% off sunglasses", "Book an Eye Checkup"]
      };
    }

    // 2. Screen Work & Computer Lenses
    if (q.includes("computer") || q.includes("screen") || q.includes("blue") || q.includes("strain")) {
      const recs = productsData.filter(p => p.category === "power-glasses" || p.id === "mc-eye-002").slice(0, 2);
      return {
        text: "For 6+ hours of daily screen time, we combine ultralight featherweight frames with German ZEISS DuraVision® BlueProtect lenses. They eliminate high-energy blue-violet glare without giving you ugly yellow-tinted vision!",
        recommendedProducts: recs,
        newSuggestions: ["Take the 2-min Eye Check", "Frames under ₹3,000", "Convertibles"]
      };
    }

    // 3. 50% Off Sunglasses
    if (q.includes("50%") || q.includes("sunglass") || q.includes("discount") || q.includes("offer") || q.includes("sale")) {
      const recs = productsData.filter(p => p.is50Off).slice(0, 2);
      return {
        text: "Our celebratory 50% off promotion is live! Use code <strong>MCHASHMA50</strong> during checkout to get flat 50% off all polarized designer sunglasses. Here are two of our most popular styles:",
        recommendedProducts: recs,
        newSuggestions: ["Show Maverick Aviator", "How to apply promo code?", "Try them on camera"]
      };
    }

    // 4. Convertibles / Magnetic Clip-ons
    if (q.includes("convertible") || q.includes("clip") || q.includes("2 in 1") || q.includes("2-in-1")) {
      const recs = productsData.filter(p => p.category === "convertibles").slice(0, 2);
      return {
        text: "M'CHASHMA Convertibles solve the hassle of carrying two pairs of glasses! They feature an ultralight titanium prescription base with rare-earth neodymium magnetic sun clips that snap on in one second flat.",
        recommendedProducts: recs,
        newSuggestions: ["Check Titanium durability", "Book Eye Checkup", "Sunglasses"]
      };
    }

    // 5. Budget Inquiries
    if (q.includes("budget") || q.includes("3000") || q.includes("cheap") || q.includes("price") || q.includes("affordable")) {
      const recs = productsData.filter(p => p.salePrice <= 3000).slice(0, 2);
      return {
        text: "Here are premium handcrafted frames under ₹3,000, all including complimentary anti-glare lenses, micro-fiber cleaning cloth, and a genuine hard case:",
        recommendedProducts: recs,
        newSuggestions: ["Zeiss lens upgrades", "Virtual Try-On", "Delivery time to Delhi"]
      };
    }

    // Default Fallback
    const recs = productsData.slice(0, 2);
    return {
      text: "I'd be glad to help you find your signature look! You can explore our catalog, test frames live on your camera in the Virtual Try-On studio, or let me know your face shape and daily routine.",
      recommendedProducts: recs,
      newSuggestions: ["What frames suit my face?", "Best for computer work", "50% off sunglasses", "Convertibles"]
    };
  }
}
