// M'CHASHMA Eyewear - Virtual Try-On Live Camera & Face Studio

export function initTryOn() {
  const video = document.getElementById("tryon-video");
  const canvas = document.getElementById("tryon-canvas");
  const fallbackImg = document.getElementById("tryon-fallback-img");
  const consentCard = document.getElementById("tryon-consent-card");
  const allowCameraBtn = document.getElementById("tryon-allow-cam-btn");
  const usePhotoBtn = document.getElementById("tryon-use-photo-btn");
  const faceGuide = document.getElementById("tryon-face-guide");
  const toggleGuideBtn = document.getElementById("tryon-toggle-guide-btn");
  const resetBtn = document.getElementById("tryon-reset-btn");
  const snapshotBtn = document.getElementById("tryon-snapshot-btn");
  const uploadInput = document.getElementById("tryon-upload-input");

  // Adjustments
  const scaleSlider = document.getElementById("tryon-scale-slider");
  const scaleValEl = document.getElementById("tryon-scale-val");
  const rotateSlider = document.getElementById("tryon-rotate-slider");
  const rotateValEl = document.getElementById("tryon-rotate-val");
  const posYSlider = document.getElementById("tryon-posy-slider");
  const posYValEl = document.getElementById("tryon-posy-val");

  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  // State
  let stream = null;
  let isCameraActive = false;
  let activeFrameImg = new Image();
  let currentFrameSrc = "assets/images/frames/frame-aviator-gold.png";
  activeFrameImg.src = currentFrameSrc;

  const defaultTransform = {
    x: 0,       // offset from center
    y: -30,     // vertical position around eyes
    scale: 1.0,
    rotation: 0 // degrees
  };

  let transform = { ...defaultTransform };

  // Drag interaction state
  let isDragging = false;
  let dragStartX = 0;
  let dragStartY = 0;

  // Set canvas coordinate resolution
  function resizeCanvas() {
    const rect = canvas.getBoundingClientRect();
    if (rect.width > 0 && rect.height > 0) {
      canvas.width = rect.width * window.devicePixelRatio;
      canvas.height = rect.height * window.devicePixelRatio;
      draw();
    }
  }
  window.addEventListener("resize", resizeCanvas);
  setTimeout(resizeCanvas, 200);

  // Draw Loop
  function draw() {
    if (!ctx) return;
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    if (activeFrameImg.complete && activeFrameImg.naturalWidth > 0) {
      ctx.save();
      const centerX = (w / 2) + (transform.x * (w / 400));
      const centerY = (h / 2) + (transform.y * (h / 400));

      ctx.translate(centerX, centerY);
      ctx.rotate((transform.rotation * Math.PI) / 180);

      const baseWidth = w * 0.58 * transform.scale;
      const aspect = activeFrameImg.naturalHeight / activeFrameImg.naturalWidth;
      const baseHeight = baseWidth * aspect;

      // Draw subtle shadow behind frame
      ctx.shadowColor = "rgba(0, 0, 0, 0.35)";
      ctx.shadowBlur = 15;
      ctx.shadowOffsetY = 6;

      ctx.drawImage(activeFrameImg, -baseWidth / 2, -baseHeight / 2, baseWidth, baseHeight);
      ctx.restore();
    }
  }

  activeFrameImg.onload = draw;

  // Listen for custom frame selection event from catalog
  window.addEventListener("set-tryon-frame", (e) => {
    if (e.detail?.frameOverlay) {
      setFrame(e.detail.frameOverlay);
    }
  });

  function setFrame(src) {
    currentFrameSrc = src;
    activeFrameImg = new Image();
    activeFrameImg.src = src;
    activeFrameImg.onload = draw;

    // Highlight selected thumbnail in list
    document.querySelectorAll(".tryon-frame-item").forEach(item => {
      const itemSrc = item.getAttribute("data-frame-src");
      item.classList.toggle("active", itemSrc === src);
    });
  }

  // Frame items in sidebar
  document.querySelectorAll(".tryon-frame-item").forEach(item => {
    item.addEventListener("click", () => {
      const src = item.getAttribute("data-frame-src");
      setFrame(src);
    });
  });

  // Slider Adjustments – these now fine‑tune the auto‑computed AR values
  if (scaleSlider) {
    scaleSlider.addEventListener("input", (e) => {
      // User‑driven scale multiplier (relative to computed scale)
      const userScale = parseFloat(e.target.value);
      transform.scale = userScale;
      if (scaleValEl) scaleValEl.textContent = `${Math.round(transform.scale * 100)}%`;
      draw();
    });
  }

  if (rotateSlider) {
    rotateSlider.addEventListener("input", (e) => {
      transform.rotation = parseFloat(e.target.value);
      if (rotateValEl) rotateValEl.textContent = `${transform.rotation}°`;
      draw();
    });
  }

  if (posYSlider) {
    posYSlider.addEventListener("input", (e) => {
      transform.y = parseFloat(e.target.value);
      if (posYValEl) posYValEl.textContent = `${transform.y}px`;
      draw();
    });
  }

  // Reset
  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      transform = { ...defaultTransform };
      if (scaleSlider) scaleSlider.value = 1.0;
      if (scaleValEl) scaleValEl.textContent = "100%";
      if (rotateSlider) rotateSlider.value = 0;
      if (rotateValEl) rotateValEl.textContent = "0°";
      if (posYSlider) posYSlider.value = -30;
      if (posYValEl) posYValEl.textContent = "-30px";
      draw();
    });
  }

  // Toggle Guide
  if (toggleGuideBtn && faceGuide) {
    toggleGuideBtn.addEventListener("click", () => {
      faceGuide.classList.toggle("hidden");
    });
  }

  // Canvas Dragging
  canvas.addEventListener("mousedown", (e) => {
    isDragging = true;
    dragStartX = e.clientX;
    dragStartY = e.clientY;
  });

  window.addEventListener("mousemove", (e) => {
    if (!isDragging) return;
    const dx = e.clientX - dragStartX;
    const dy = e.clientY - dragStartY;
    dragStartX = e.clientX;
    dragStartY = e.clientY;

    transform.x += dx * 0.8;
    transform.y += dy * 0.8;
    if (posYSlider) posYSlider.value = Math.round(transform.y);
    if (posYValEl) posYValEl.textContent = `${Math.round(transform.y)}px`;
    draw();
  });

  window.addEventListener("mouseup", () => {
    isDragging = false;
  });

  // Touch Support for Mobile
  canvas.addEventListener("touchstart", (e) => {
    if (e.touches.length === 1) {
      isDragging = true;
      dragStartX = e.touches[0].clientX;
      dragStartY = e.touches[0].clientY;
    }
  }, { passive: true });

  canvas.addEventListener("touchmove", (e) => {
    if (!isDragging || e.touches.length !== 1) return;
    const dx = e.touches[0].clientX - dragStartX;
    const dy = e.touches[0].clientY - dragStartY;
    dragStartX = e.touches[0].clientX;
    dragStartY = e.touches[0].clientY;

    transform.x += dx * 0.8;
    transform.y += dy * 0.8;
    draw();
  }, { passive: true });

  canvas.addEventListener("touchend", () => {
    isDragging = false;
  });

  // Camera Activation
  if (allowCameraBtn) {
    allowCameraBtn.addEventListener("click", startCamera);
  }

  async function startCamera() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      showCameraError("Your web browser does not support live camera access. Please use the high-definition photo models or upload your photo.");
      return;
    }

    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: "user",
          width: { ideal: 1280 },
          height: { ideal: 720 }
        },
        audio: false
      });

      if (video) {
        video.srcObject = stream;
        await video.play();
        video.classList.add("active");
      }

      // Lazy‑load MediaPipe FaceMesh wrapper and start tracking
      if (!window._faceTracker) {
        const module = await import("./faceTracker.js");
        window._faceTracker = module;
      }
      window._faceTracker.start(video, handleFaceResults);

      if (fallbackImg) fallbackImg.style.display = "none";
      if (consentCard) consentCard.classList.add("hidden");
      isCameraActive = true;
      resizeCanvas();
    } catch (err) {
      console.warn("Camera access denied or unavailable:", err);
      showCameraError("Camera permission was denied or camera device is in use. We've switched you to our high-resolution model preview.");
      useFallbackPhoto();
    }
  }

  // Process MediaPipe results and update the frame transform
  function handleFaceResults(results) {
    if (!results.multiFaceLandmarks || results.multiFaceLandmarks.length === 0) return;
    const landmarks = results.multiFaceLandmarks[0];
    const w = canvas.width;
    const h = canvas.height;

    const leftEye = landmarks[33];
    const rightEye = landmarks[263];
    const nose = landmarks[1];

    const lx = leftEye.x * w;
    const ly = leftEye.y * h;
    const rx = rightEye.x * w;
    const ry = rightEye.y * h;
    const nx = nose.x * w;
    const ny = nose.y * h;

    const cx = (lx + rx) / 2;
    const cy = (ly + ry) / 2;

    const eyeDist = Math.hypot(rx - lx, ry - ly);
    const baseEyeDist = w * 0.58;
    const computedScale = eyeDist / baseEyeDist;

    const angleRad = Math.atan2(ry - ly, rx - lx);
    const computedRot = angleRad * 180 / Math.PI;

    const offsetX = (cx - w / 2) * (400 / w);
    const offsetY = (cy - h / 2) * (400 / h);

    transform.x = offsetX;
    transform.y = offsetY;
    transform.scale = computedScale;
    transform.rotation = computedRot;

    if (scaleSlider) scaleSlider.value = transform.scale.toFixed(2);
    if (scaleValEl) scaleValEl.textContent = `${Math.round(transform.scale * 100)}%`;
    if (rotateSlider) rotateSlider.value = Math.round(transform.rotation);
    if (rotateValEl) rotateValEl.textContent = `${Math.round(transform.rotation)}°`;
    if (posYSlider) posYSlider.value = Math.round(transform.y);
    if (posYValEl) posYValEl.textContent = `${Math.round(transform.y)}px`;

    draw();
  }

  function showCameraError(msg) {
    window.dispatchEvent(new CustomEvent("show-toast", {
      detail: { message: msg, type: "danger" }
    }));
  }

  function useFallbackPhoto() {
    if (stream) {
      stream.getTracks().forEach(t => t.stop());
      stream = null;
    }
    if (video) {
      video.pause();
      video.classList.remove("active");
    }
    if (fallbackImg) fallbackImg.style.display = "block";
    if (consentCard) consentCard.classList.add("hidden");
    isCameraActive = false;
    resizeCanvas();
  }

  if (usePhotoBtn) {
    usePhotoBtn.addEventListener("click", useFallbackPhoto);
  }

  // Model Picker
  document.querySelectorAll(".tryon-model-thumb").forEach(thumb => {
    thumb.addEventListener("click", () => {
      document.querySelectorAll(".tryon-model-thumb").forEach(t => t.classList.remove("active"));
      thumb.classList.add("active");
      const modelSrc = thumb.getAttribute("data-model-src");
      if (fallbackImg) {
        fallbackImg.src = modelSrc;
        useFallbackPhoto();
      }
    });
  });

  // Upload Own Face Photo
  if (uploadInput) {
    uploadInput.addEventListener("change", (e) => {
      const file = e.target.files?.[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (event) => {
          if (fallbackImg && event.target?.result) {
            fallbackImg.src = event.target.result;
            useFallbackPhoto();
            window.dispatchEvent(new CustomEvent("show-toast", {
              detail: { message: "Photo loaded! Privacy note: Image is processed locally only.", type: "success" }
            }));
          }
        };
        reader.readAsDataURL(file);
      }
    });
  }

  // Snapshot Capture
  if (snapshotBtn) {
    snapshotBtn.addEventListener("click", () => {
      const exportCanvas = document.createElement("canvas");
      exportCanvas.width = 1200;
      exportCanvas.height = 900;
      const exCtx = exportCanvas.getContext("2d");
      if (!exCtx) return;

      // Draw background (video or photo)
      if (isCameraActive && video) {
        exCtx.save();
        exCtx.translate(exportCanvas.width, 0);
        exCtx.scale(-1, 1);
        exCtx.drawImage(video, 0, 0, exportCanvas.width, exportCanvas.height);
        exCtx.restore();
      } else if (fallbackImg) {
        exCtx.drawImage(fallbackImg, 0, 0, exportCanvas.width, exportCanvas.height);
      }

      // Draw frame on export canvas
      const w = exportCanvas.width;
      const h = exportCanvas.height;
      exCtx.save();
      const centerX = (w / 2) + (transform.x * (w / 400));
      const centerY = (h / 2) + (transform.y * (h / 400));

      exCtx.translate(centerX, centerY);
      exCtx.rotate((transform.rotation * Math.PI) / 180);

      const baseWidth = w * 0.58 * transform.scale;
      const aspect = activeFrameImg.naturalHeight / activeFrameImg.naturalWidth;
      const baseHeight = baseWidth * aspect;

      exCtx.shadowColor = "rgba(0, 0, 0, 0.4)";
      exCtx.shadowBlur = 18;
      exCtx.shadowOffsetY = 8;
      exCtx.drawImage(activeFrameImg, -baseWidth / 2, -baseHeight / 2, baseWidth, baseHeight);
      exCtx.restore();

      // Brand Watermark
      exCtx.fillStyle = "rgba(15, 23, 42, 0.85)";
      exCtx.roundRect(w - 280, h - 70, 250, 48, 12);
      exCtx.fill();
      exCtx.fillStyle = "#FFFFFF";
      exCtx.font = "bold 20px Outfit, sans-serif";
      exCtx.fillText("M'CHASHMA EYEWEAR", w - 260, h - 38);

      // Trigger Download
      const link = document.createElement("a");
      link.download = `mchashma-tryon-${Date.now()}.jpg`;
      link.href = exportCanvas.toDataURL("image/jpeg", 0.92);
      link.click();

      window.dispatchEvent(new CustomEvent("show-toast", {
        detail: { message: "Snapshot saved to your device!", type: "success" }
      }));
    });
  }
}
