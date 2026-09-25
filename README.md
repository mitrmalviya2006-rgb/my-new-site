# M’CHASHMA Eyewear — Premium Optical E-Commerce Storefront

A high-performance, polished e-commerce website for **M’CHASHMA Eyewear**, an Indian eyewear retailer and certified Carl Zeiss Vision Partner.

---

## 👓 Brand Identity & Store Aesthetics

Built to mirror M’CHASHMA’s real-world flagship optical stores:
- **Bright White Displays**: Clean, gallery-grade product podiums and crisp display counters (`#FFFFFF`, `#F8FAFC`).
- **Architectural Charcoal Accents**: Slate and midnight tones (`#0F172A`, `#1E293B`) providing depth and grounding.
- **Controlled Merchandising Yellow**: Inspired by the store’s illuminated **"Premium Blinkers"** frame showcases (`#F59E0B`, `#FBBF24`).
- **Signature M’CHASHMA Red**: Distinctive brand red logo (`#E11D48`) placed across the header, intro mark, watermarks, and primary CTAs.
- **Interactive 3D Depth**: Every button and link features rounded corners, tactile depth, and a responsive 3D hover pop.
- **Dual Themes**: Complete light and dark mode support with instant switching.

---

## 🌟 Key Features & Experiences

### 1. Brand Navigation & Sticky Header
- Prominently displays the official **M’CHASHMA** logo.
- Sticky navigation bar with links:
  - **Home**, **Shop**, **Eyeglasses**, **Sunglasses (50% Off)**, **Power Glasses**, **Convertibles**, **Virtual Try-On**, **Eye Check**, **Store**, **Cart**.
- Real-time **Search Bar** with instant dropdown autocomplete (search by frame name, shape, material, or color).
- One-click **Light/Dark Theme Switcher**.
- Dynamic **Cart Count Badge** with pop animation.

### 2. Immersive Hero & Scroll-Driven Brand Intro
- **Scroll-driven intro animation** that reveals the M’CHASHMA mark and draws a vector spectacle outline.
- Hero section powered by real store photography (`store-hero-wide.jpg` from `ad.jpeg`) with sleek optical glassmorphism.
- Headline: *"Find frames that feel like you."*
- Primary CTAs: **"Shop frames"** and **"Try them on"**.
- Promotional banner with live countdown and coupon code `MCHASHMA50` for 50% off sunglasses.

### 3. Alternating Scroll-Driven Product Storytelling
- **Convertibles Showcase**: Highlights the 2-in-1 titanium optical frame with rare-earth neodymium magnetic polarized sun clip.
- **Zeiss Refraction Clinic**: Features real clinical photography (`store-refraction-clinic.jpg`) and Zeiss 0.12D wavefront refraction.

### 4. Searchable Shop Catalog & Live Filters
- Believable catalog with prices in **INR (₹)** and real optical attributes:
  - **Category**: Eyeglasses, Sunglasses, Power Glasses, Convertibles
  - **Gender**: Men, Women, Unisex
  - **Frame Shapes**: Aviator, Wayfarer, Round, Rectangle, Hexagonal, Cat-Eye
  - **Materials**: Pure Titanium, Bio-Acetate, Lightweight Metal
  - **Colors**: Obsidian Black, 24K Gold, Silver Chrome, Havana Tortoise, Rose Gold, Crystal, Burgundy
  - **Price Range Slider**: Dynamic slider from ₹1,500 to ₹6,000+
  - **Prescription Compatible Toggle**
- **3D Product Cards**: Rounded corners, depth, 3D hover lift, quick add-to-cart, wishlist heart toggle, and direct "Try On" camera shortcut.

### 5. Product Detail Modal
- Multi-angle high-resolution image gallery with thumbnail switcher.
- Color swatch selector.
- Detailed frame fitting dimensions (Lens Width, Bridge, Temple, Total Width, Frame Weight).
- Prescription selection: Single Vision, Progressive, Zero Power Screen.
- Lens Package Upgrades:
  - Anti-Glare Standard (Free)
  - M'CHASHMA BlueCut™ Digital Shield (+₹999)
  - German ZEISS DuraVision® Platinum (+₹2,499)
  - Transitions® Light Intelligent (+₹2,999)
- Indian Pincode delivery checker with instant delivery estimate.
- Direct "Buy Now" and "Add to Cart" actions.

### 6. Browser-Camera Virtual Try-On Studio
- **Working Live Webcam Stream**: Requests camera access with clear user consent text and privacy assurance (*frames are never recorded or transmitted to servers*).
- **Interactive Eyewear Overlay**:
  - Live drag-and-drop position adjustment.
  - Scale / size slider (70% - 140%).
  - Tilt angle rotation slider (-20° to +20°).
  - Vertical height adjuster.
  - Instant Reset button.
- **Face Alignment Guide**: Toggleable dashed oval guide with horizontal eye alignment line.
- **Studio Model Fallbacks**: Choose between high-definition portraits of Indian female and male models.
- **Photo Upload**: Allows users to upload their own photo for private local preview.
- **Snapshot Export**: Download a high-res photo with the fitted eyewear frame and official M'CHASHMA watermark.

### 7. Smart Eye Check (Feyenally-Inspired Concept)
- Step-by-step digital vision screening flow:
  1. **Calibration & Guidance**: 75%+ brightness tip, 40-50 cm arm's length viewing guide, daily glasses guidance.
  2. **Lifestyle Questionnaire**: Screen hours, headaches, night driving glare.
  3. **Tumbling E Visual Acuity Test**: Interactive 4-directional test (Up, Down, Left, Right) scaling down from 20/100 to 20/20.
  4. **Astigmatism Clock Dial Test**: Radial spokes test for astigmatic distortion.
  5. **Clinical Summary & Results**: Visual acuity score, digital strain index, personalized Zeiss lens recommendation, and **"Book an Eye Checkup"** modal for in-store Zeiss refraction.

### 8. Floating AI Eyewear Assistant ("M’CHASHMA Guide")
- Floating widget with glowing pulse ring and badge.
- Instant conversational starters:
  - *"What frames suit an Oval face?"*
  - *"Best lenses for heavy computer screen work?"*
  - *"Show me 50% off sunglasses"*
  - *"How do 2-in-1 Convertibles work?"*
  - *"Frames under ₹3,000"*
- Returns personalized conversational guidance with **interactive product recommendation cards** directly inside the chat.

### 9. Cart & Multi-Step Checkout
- Slide-out Cart Drawer persisting in `localStorage`.
- Quantity modification (+ / -) and item removal.
- Promo coupon code `MCHASHMA50` automatically deducts 50% from all sunglasses.
- Free shipping progress bar (unlocks free delivery over ₹999).
- Multi-step checkout with address validation, prescription upload choice, and payment selection (UPI / RuPay / Cards / Cash on Delivery).
- Order confirmation screen with generated Order ID (e.g. `MC-IND-739281`) and estimated dispatch timeline.

### 10. Store Experience & Flagship Showrooms
- Gallery featuring real store photography:
  - `store-hero-wide.jpg` (from `ad.jpeg`)
  - `store-display-stand.jpg` (from `daa.jpeg`)
  - `store-zeiss-showcase.jpg` (from `h.jpeg`)
  - `store-refraction-clinic.jpg` (refraction suite)
- Store amenities, opening hours (Mon-Sun 10:30 AM - 9:30 PM), customer reviews, and appointment booking form.

---

## 🚀 How to Run Locally

Since this application is built with pure standards-based **HTML5, Vanilla CSS, and modern ES6 JavaScript**, it runs without requiring Node.js or complex build tooling.

### Starting the Server:

Open PowerShell or Terminal in the project directory:

```bash
cd "C:\Users\Mitr\.gemini\antigravity-ide\scratch\mchashma-eyewear"
python server.py
```

Then open your browser and navigate to:
```
http://127.0.0.1:8080
```

Alternatively, you can open `index.html` directly in any modern web browser.

---

## 📁 Project Architecture

```
mchashma-eyewear/
├── index.html                  # Main semantic HTML5 document
├── server.py                   # Lightweight local Python server (CORS & ES module support)
├── README.md                   # Documentation and running guide
└── assets/
    ├── css/
    │   ├── variables.css       # Tokens, colors, 3D shadows, light/dark themes
    │   ├── reset.css           # Global CSS reset & accessibility
    │   ├── components.css      # 3D buttons, badges, pop links, cards, modals, toasts
    │   ├── header.css          # Sticky header, search dropdown, promo banner
    │   ├── hero.css            # Store hero banner & scroll intro animation
    │   ├── catalog.css         # Shop layout, live filters, 3D product cards
    │   ├── tryon.css           # Webcam preview, canvas overlay, sliders, face guide
    │   ├── eyecheck.css        # Feyenally-inspired vision charts, Tumbling E, astigmatism dial
    │   ├── aiguide.css         # Floating M'CHASHMA Guide AI widget & chat drawer
    │   ├── store.css           # Store photo gallery, storytelling, customer reviews
    │   └── footer.css          # Detailed store footer, policies, payment badges
    ├── js/
    │   ├── app.js              # Application coordinator & scroll observers
    │   ├── data/
    │   │   ├── products.js     # Believable product catalog (INR prices, specs)
    │   │   └── storeInfo.js    # Showroom locations, hours, reviews, amenities
    │   ├── utils/
    │   │   └── storage.js      # LocalStorage cart, wishlist, theme, coupon logic
    │   └── components/
    │       ├── header.js       # Sticky header, search autocomplete, theme switcher
    │       ├── catalog.js      # Live filter engine, 3D card render, sort
    │       ├── productModal.js # Product detail view, lens packages, pincode checker
    │       ├── cart.js         # Cart drawer, MCHASHMA50 coupon, checkout flow
    │       ├── tryon.js        # Camera stream, canvas rendering, face guide, snapshot
    │       ├── eyeCheck.js     # Vision screening tests (Tumbling E, Astigmatism, Acuity)
    │       ├── aiGuide.js      # Conversational AI assistant & recommendations
    │       └── storeSection.js # Showroom gallery & in-store exam booking modal
    └── images/
        ├── store-hero-wide.jpg         # Real store photo (ad.jpeg)
        ├── store-display-stand.jpg     # Real store photo (daa.jpeg)
        ├── store-zeiss-showcase.jpg    # Real store photo (h.jpeg)
        ├── store-refraction-clinic.jpg # Zeiss eye examination suite
        ├── mchashma-logo.png           # Transparent M'CHASHMA logo
        ├── lifestyle-hero-sunglasses.jpg
        ├── product-convertibles-hero.jpg
        ├── model-female-tryon.jpg      # Try-on model (female)
        ├── model-male-tryon.jpg        # Try-on model (male)
        ├── product-aviator-sunglasses.jpg
        ├── product-crystal-eyeglasses.jpg
        ├── products/                   # Studio product card previews
        └── frames/                     # Transparent PNG eyewear frame overlays
```
