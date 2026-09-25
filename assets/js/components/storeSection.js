// M'CHASHMA Eyewear - Store Locator, Gallery & Appointment Booking

import { storeInfo } from "../data/storeInfo.js";

export function initStoreSection() {
  const bookingModal = document.getElementById("booking-modal");
  const bookingCloseBtn = document.getElementById("booking-close-btn");
  const bookingForm = document.getElementById("booking-form");

  function openBookingModal() {
    bookingModal?.classList.add("active");
    document.body.style.overflow = "hidden";
  }

  function closeBookingModal() {
    bookingModal?.classList.remove("active");
    document.body.style.overflow = "";
  }

  document.getElementById("nav-book-appointment-btn")?.addEventListener("click", openBookingModal);
  window.addEventListener("open-booking-modal", openBookingModal);

  bookingCloseBtn?.addEventListener("click", closeBookingModal);
  bookingModal?.addEventListener("click", (e) => {
    if (e.target === bookingModal) closeBookingModal();
  });

  // Handle Booking Form Submission
  if (bookingForm) {
    bookingForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const branch = document.getElementById("booking-branch")?.value;
      const date = document.getElementById("booking-date")?.value;
      const time = document.getElementById("booking-time")?.value;
      const name = document.getElementById("booking-name")?.value;

      closeBookingModal();

      window.dispatchEvent(new CustomEvent("show-toast", {
        detail: {
          message: `Appointment booked for ${name} at ${branch} on ${date} (${time})! SMS details sent.`,
          type: "success"
        }
      }));
    });
  }
}
