/* MentorBridge — glassmorphic booking modal + AJAX submission with success animation. */
(function () {
  'use strict';

  const modal = document.getElementById('bookingModal');
  if (!modal) return;

  const openers = document.querySelectorAll('[data-open-booking]');
  const closers = document.querySelectorAll('[data-close-booking]');
  const body = document.getElementById('modalBookingBody');
  const success = document.getElementById('bookingSuccess');
  const form = document.getElementById('bookingFormModal');
  let lastFocused = null;

  function open() {
    lastFocused = document.activeElement;
    if (body) body.hidden = false;
    if (success) success.hidden = true;
    modal.hidden = false;
    document.body.style.overflow = 'hidden';
    const first = form && form.querySelector('input[name="topic"]');
    if (first) first.focus();
  }

  function close() {
    modal.hidden = true;
    document.body.style.overflow = '';
    if (lastFocused && lastFocused.focus) lastFocused.focus();
  }

  openers.forEach(function (btn) { btn.addEventListener('click', open); });
  closers.forEach(function (btn) { btn.addEventListener('click', close); });
  modal.addEventListener('click', function (event) { if (event.target === modal) close(); });
  document.addEventListener('keydown', function (event) { if (event.key === 'Escape' && !modal.hidden) close(); });

  if (form) {
    form.addEventListener('submit', function (event) {
      event.preventDefault();
      const endpoint = form.dataset.endpoint;
      const submit = form.querySelector('button[type="submit"]');
      if (submit) { submit.disabled = true; submit.textContent = 'Sending request…'; }

      fetch(endpoint, { method: 'POST', body: new FormData(form), credentials: 'same-origin' })
        .then(function (response) {
          // A successful booking redirects to /dashboard?booked=1; validation errors
          // redirect back to the mentor profile. Detect by final URL.
          if (!response.ok || response.url.indexOf('/dashboard') === -1) {
            throw new Error('Please check the form fields and try again.');
          }
          if (body) body.hidden = true;
          if (success) success.hidden = false;
        })
        .catch(function (error) {
          let note = form.querySelector('.form-error');
          if (!note) {
            note = document.createElement('p');
            note.className = 'form-error muted small';
            form.appendChild(note);
          }
          note.textContent = error.message || 'Could not send the request. Please try again.';
          if (submit) { submit.disabled = false; submit.textContent = 'Send request →'; }
        });
    });
  }
})();
