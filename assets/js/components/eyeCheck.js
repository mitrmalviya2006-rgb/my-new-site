// M'CHASHMA Eyewear - Eye Check Digital Vision Screening (Feyenally Concept)

import { storeInfo } from "../data/storeInfo.js";

export function initEyeCheck() {
  const container = document.getElementById("eyecheck-root");
  if (!container) return;

  // Screening State
  const testState = {
    step: 1, // 1: Guidance & Setup, 2: Questionnaire, 3: Tumbling E Acuity, 4: Astigmatism Dial, 5: Results
    answers: {
      screenHours: "6-8",
      headaches: "sometimes",
      nightDrivingGlare: "yes",
      currentGlasses: "yes"
    },
    acuityRound: 0,
    acuityScore: 0,
    currentDirection: "up", // 'up', 'down', 'left', 'right'
    astigmatismNoticed: false,
    estimatedAcuity: "20/20"
  };

  const acuityLevels = [
    { label: "20/100", size: 90, rotation: 0 },
    { label: "20/60",  size: 64, rotation: 90 },
    { label: "20/40",  size: 46, rotation: 180 },
    { label: "20/25",  size: 32, rotation: 270 },
    { label: "20/20",  size: 24, rotation: 0 }
  ];

  function render() {
    container.innerHTML = `
      <div class="eyecheck-container">
        <!-- Medical Disclaimer -->
        <div class="eyecheck-disclaimer-box">
          <div class="disclaimer-icon">⚠️</div>
          <div class="disclaimer-text">
            <strong>Important Optical Screening Disclaimer:</strong> This digital screening tool is inspired by modern visual assessment apps and provides educational guidance on visual comfort and digital eye fatigue. It is <strong>not a medical diagnosis</strong> and does not replace a comprehensive clinical refraction by a licensed optometrist or ophthalmologist.
          </div>
        </div>

        <!-- Stepper -->
        <div class="eyecheck-stepper">
          <div class="stepper-step ${testState.step >= 1 ? 'active' : ''} ${testState.step > 1 ? 'completed' : ''}">
            <div class="step-circle">1</div>
            <div class="step-label">Calibration</div>
          </div>
          <div class="stepper-step ${testState.step >= 2 ? 'active' : ''} ${testState.step > 2 ? 'completed' : ''}">
            <div class="step-circle">2</div>
            <div class="step-label">Lifestyle Qs</div>
          </div>
          <div class="stepper-step ${testState.step >= 3 ? 'active' : ''} ${testState.step > 3 ? 'completed' : ''}">
            <div class="step-circle">3</div>
            <div class="step-label">Acuity Test</div>
          </div>
          <div class="stepper-step ${testState.step >= 4 ? 'active' : ''} ${testState.step > 4 ? 'completed' : ''}">
            <div class="step-circle">4</div>
            <div class="step-label">Astigmatism</div>
          </div>
          <div class="stepper-step ${testState.step >= 5 ? 'active' : ''}">
            <div class="step-circle">5</div>
            <div class="step-label">Results</div>
          </div>
        </div>

        <!-- Step Views -->
        ${renderStepContent()}
      </div>
    `;

    attachEvents();
  }

  function renderStepContent() {
    switch (testState.step) {
      case 1:
        return `
          <div class="eyecheck-step-view active">
            <h3 style="font-family: var(--font-heading); font-size: 1.5rem; font-weight: 800; text-align: center; margin-bottom: 8px;">
              Screen Preparation & Viewing Distance
            </h3>
            <p style="text-align: center; color: var(--text-secondary); font-size: 0.95rem; margin-bottom: 28px;">
              For accurate optical measurement, set up your device in a well-lit room.
            </p>

            <div class="guidance-card">
              <div class="guidance-item">
                <div class="guidance-icon">💡</div>
                <div class="guidance-title">Set 75%+ Brightness</div>
                <div class="guidance-text">Turn off night mode, blue-light filter, or True Tone during this test.</div>
              </div>
              <div class="guidance-item">
                <div class="guidance-icon">📏</div>
                <div class="guidance-title">Arm's Length (40-50 cm)</div>
                <div class="guidance-text">Hold your screen at comfortable reading distance directly at eye level.</div>
              </div>
              <div class="guidance-item">
                <div class="guidance-icon">👓</div>
                <div class="guidance-title">Wear Daily Glasses</div>
                <div class="guidance-text">If you currently wear contact lenses or glasses, keep them on to test corrected acuity.</div>
              </div>
            </div>

            <div style="text-align: center; margin-top: 30px;">
              <button id="step1-next-btn" class="btn btn-primary btn-lg">
                I'm Ready, Start Vision Check →
              </button>
            </div>
          </div>
        `;

      case 2:
        return `
          <div class="eyecheck-step-view active">
            <h3 style="font-family: var(--font-heading); font-size: 1.5rem; font-weight: 800; margin-bottom: 8px;">
              Visual Lifestyle Questionnaire
            </h3>
            <p style="color: var(--text-secondary); font-size: 0.92rem; margin-bottom: 24px;">
              Helps evaluate digital eye strain and recommend customized Zeiss optical filters.
            </p>

            <div style="display: flex; flex-direction: column; gap: 20px;">
              <div>
                <label class="form-label">How many hours a day do you spend looking at digital screens?</label>
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 6px;">
                  ${['< 4 hours', '4-6 hours', '6-8 hours', '8+ hours'].map(val => `
                    <button class="btn btn-glass btn-sm q-btn ${testState.answers.screenHours === val ? 'active' : ''}" data-q="screenHours" data-val="${val}">${val}</button>
                  `).join('')}
                </div>
              </div>

              <div>
                <label class="form-label">Do you experience eye dryness, tiredness, or mild headaches by evening?</label>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 6px;">
                  ${['Never', 'Sometimes', 'Frequently'].map(val => `
                    <button class="btn btn-glass btn-sm q-btn ${testState.answers.headaches === val.toLowerCase() ? 'active' : ''}" data-q="headaches" data-val="${val.toLowerCase()}">${val}</button>
                  `).join('')}
                </div>
              </div>

              <div>
                <label class="form-label">Do you notice glare, halos, or starbursts around headlights while driving at night?</label>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 6px;">
                  ${['Yes, often', 'Occasionally', 'Never'].map(val => `
                    <button class="btn btn-glass btn-sm q-btn ${testState.answers.nightDrivingGlare === val.toLowerCase() ? 'active' : ''}" data-q="nightDrivingGlare" data-val="${val.toLowerCase()}">${val}</button>
                  `).join('')}
                </div>
              </div>
            </div>

            <div style="display: flex; justify-content: space-between; margin-top: 36px;">
              <button id="step2-prev-btn" class="btn btn-glass btn-sm">← Back</button>
              <button id="step2-next-btn" class="btn btn-primary">Proceed to Acuity Chart →</button>
            </div>
          </div>
        `;

      case 3:
        const currentLevel = acuityLevels[testState.acuityRound];
        const rot = currentLevel.rotation;
        return `
          <div class="eyecheck-step-view active" style="text-align: center;">
            <div style="font-size: 0.82rem; font-weight: 700; color: var(--brand-red); text-transform: uppercase; margin-bottom: 6px;">
              Acuity Stage ${testState.acuityRound + 1} of ${acuityLevels.length} • Testing Target: ${currentLevel.label}
            </div>
            <h3 style="font-family: var(--font-heading); font-size: 1.45rem; font-weight: 800; margin-bottom: 6px;">
              Which direction are the prongs of the "E" pointing?
            </h3>
            <p style="color: var(--text-muted); font-size: 0.88rem; margin-bottom: 24px;">
              Cover your left eye first, or keep both eyes open at arm's length. Click the matching direction button below.
            </p>

            <div class="chart-testing-stage">
              <div class="chart-symbol-e" style="font-size: ${currentLevel.size}px; transform: rotate(${rot}deg);">
                E
              </div>
            </div>

            <div class="direction-controls-grid">
              <button class="btn-direction" data-dir="up" title="Up">▲</button>
              <button class="btn-direction" data-dir="right" title="Right">▶</button>
              <button class="btn-direction" data-dir="down" title="Down">▼</button>
              <button class="btn-direction" data-dir="left" title="Left">◀</button>
            </div>

            <button id="cant-see-btn" class="btn btn-glass btn-sm">
              I can't see this clearly (Skip)
            </button>
          </div>
        `;

      case 4:
        return `
          <div class="eyecheck-step-view active" style="text-align: center;">
            <div style="font-size: 0.82rem; font-weight: 700; color: var(--brand-yellow); text-transform: uppercase; margin-bottom: 6px;">
              Stage 4: Astigmatism Dial Screening
            </div>
            <h3 style="font-family: var(--font-heading); font-size: 1.45rem; font-weight: 800; margin-bottom: 8px;">
              Do any of the radial spoke lines appear darker or thicker than the others?
            </h3>
            <p style="color: var(--text-muted); font-size: 0.88rem; max-width: 500px; margin: 0 auto 20px;">
              Look at the center dot. If some lines appear sharp & dark while others look lighter or blurred, this may suggest corneal astigmatism.
            </p>

            <div class="astigmatism-stage">
              <svg class="astigmatism-dial-svg" viewBox="0 0 200 200">
                <circle cx="100" cy="100" r="95" fill="none" stroke="var(--border-subtle)" stroke-width="2"/>
                ${[0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165].map(angle => `
                  <line x1="100" y1="100" x2="${100 + 85 * Math.cos(angle * Math.PI / 180)}" y2="${100 + 85 * Math.sin(angle * Math.PI / 180)}" stroke="var(--text-primary)" stroke-width="2.5" />
                  <line x1="100" y1="100" x2="${100 - 85 * Math.cos(angle * Math.PI / 180)}" y2="${100 - 85 * Math.sin(angle * Math.PI / 180)}" stroke="var(--text-primary)" stroke-width="2.5" />
                `).join('')}
                <circle cx="100" cy="100" r="6" fill="var(--brand-red)" />
              </svg>
            </div>

            <div style="display: flex; justify-content: center; gap: 16px; margin-top: 24px;">
              <button id="astigmatism-no-btn" class="btn btn-glass">All lines look equally uniform</button>
              <button id="astigmatism-yes-btn" class="btn btn-primary">Yes, some lines appear darker</button>
            </div>
          </div>
        `;

      case 5:
        return `
          <div class="eyecheck-step-view active">
            <h3 style="font-family: var(--font-heading); font-size: 1.6rem; font-weight: 800; text-align: center; margin-bottom: 6px;">
              Your Optical Wellness Summary
            </h3>
            <p style="text-align: center; color: var(--text-muted); font-size: 0.9rem; margin-bottom: 28px;">
              Based on your responses and the Tumbling E acuity chart screening.
            </p>

            <div class="eyecheck-results-card">
              <div class="results-score-row">
                <div class="score-metric-box">
                  <div class="metric-val">${testState.estimatedAcuity}</div>
                  <div class="metric-title">Estimated Acuity</div>
                  <div style="font-size: 0.76rem; color: #10B981; margin-top: 4px;">✓ Good functional range</div>
                </div>
                <div class="score-metric-box">
                  <div class="metric-val" style="color: var(--brand-yellow);">${testState.answers.screenHours === '8+ hours' ? 'High' : 'Moderate'}</div>
                  <div class="metric-title">Digital Eye Strain</div>
                  <div style="font-size: 0.76rem; color: var(--text-muted); margin-top: 4px;">${testState.answers.screenHours} daily screen time</div>
                </div>
                <div class="score-metric-box">
                  <div class="metric-val" style="color: #3B82F6;">${testState.astigmatismNoticed ? 'Check' : 'Low'}</div>
                  <div class="metric-title">Astigmatism Index</div>
                  <div style="font-size: 0.76rem; color: var(--text-muted); margin-top: 4px;">${testState.astigmatismNoticed ? 'Refraction advised' : 'Symmetrical'}</div>
                </div>
              </div>

              <div style="background: var(--bg-card); border-radius: var(--radius-md); padding: 18px; border: 1px solid var(--border-subtle); margin-bottom: 24px;">
                <h4 style="font-size: 1rem; font-weight: 700; margin-bottom: 8px; color: var(--text-primary); display: flex; align-items: center; gap: 8px;">
                  👓 Recommended Lens Solution:
                  <span class="badge badge-zeiss">ZEISS DuraVision® BlueProtect</span>
                </h4>
                <p style="font-size: 0.88rem; color: var(--text-secondary); line-height: 1.5;">
                  Given your ${testState.answers.screenHours} screen usage and reported symptoms, we recommend ZEISS precision lenses with high-contrast anti-reflective coatings. These filter harsh HEV artificial blue wavelengths without distorting color accuracy.
                </p>
              </div>

              <!-- Store Appointment CTA -->
              <div class="clinic-booking-banner">
                <div class="clinic-banner-content">
                  <h4>Schedule In-Store Zeiss Refraction Checkup</h4>
                  <p>Visit our flagship Connaught Place or Bandra store for a complimentary 12-point clinical eye examination.</p>
                </div>
                <button id="book-store-checkup-btn" class="btn btn-yellow">
                  Book Free Eye Checkup
                </button>
              </div>
            </div>

            <div style="text-align: center;">
              <button id="retake-test-btn" class="btn btn-glass btn-sm">Retake Screening</button>
            </div>
          </div>
        `;
    }
  }

  function attachEvents() {
    // Step 1 -> Step 2
    document.getElementById("step1-next-btn")?.addEventListener("click", () => {
      testState.step = 2;
      render();
    });

    // Step 2 Question Choices
    document.querySelectorAll(".q-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const q = btn.getAttribute("data-q");
        const val = btn.getAttribute("data-val");
        testState.answers[q] = val;
        btn.parentElement.querySelectorAll(".q-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
      });
    });

    document.getElementById("step2-prev-btn")?.addEventListener("click", () => {
      testState.step = 1;
      render();
    });

    document.getElementById("step2-next-btn")?.addEventListener("click", () => {
      testState.step = 3;
      testState.acuityRound = 0;
      testState.acuityScore = 0;
      render();
    });

    // Step 3 Direction buttons
    const directionRotMap = {
      0: "right",
      90: "down",
      180: "left",
      270: "up"
    };

    document.querySelectorAll(".btn-direction").forEach(btn => {
      btn.addEventListener("click", () => {
        const chosenDir = btn.getAttribute("data-dir");
        const currentRot = acuityLevels[testState.acuityRound].rotation;
        const correctDir = directionRotMap[currentRot];

        if (chosenDir === correctDir) {
          testState.acuityScore++;
        }

        if (testState.acuityRound < acuityLevels.length - 1) {
          testState.acuityRound++;
          render();
        } else {
          // Finished acuity
          testState.estimatedAcuity = testState.acuityScore >= 4 ? "20/20" : (testState.acuityScore >= 2 ? "20/30" : "20/50");
          testState.step = 4;
          render();
        }
      });
    });

    document.getElementById("cant-see-btn")?.addEventListener("click", () => {
      testState.estimatedAcuity = testState.acuityScore >= 3 ? "20/25" : "20/40";
      testState.step = 4;
      render();
    });

    // Step 4 Astigmatism
    document.getElementById("astigmatism-no-btn")?.addEventListener("click", () => {
      testState.astigmatismNoticed = false;
      testState.step = 5;
      render();
    });

    document.getElementById("astigmatism-yes-btn")?.addEventListener("click", () => {
      testState.astigmatismNoticed = true;
      testState.step = 5;
      render();
    });

    // Step 5 Actions
    document.getElementById("retake-test-btn")?.addEventListener("click", () => {
      testState.step = 1;
      render();
    });

    document.getElementById("book-store-checkup-btn")?.addEventListener("click", () => {
      window.dispatchEvent(new CustomEvent("open-booking-modal"));
    });
  }

  // Initial Render
  render();
}
