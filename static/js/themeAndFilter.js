/* MentorBridge — theme switcher, instant filters and lightweight micro-interactions.
   Vanilla JS only. No frameworks, no build step. */
(function () {
  'use strict';

  /* ---------- Dark / light mode ---------- */
  const root = document.documentElement;
  const toggle = document.getElementById('themeToggle');

  function syncToggle() {
    if (!toggle) return;
    const dark = root.dataset.theme === 'dark';
    toggle.setAttribute('aria-checked', String(dark));
    toggle.setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode');
  }
  syncToggle();

  if (toggle) {
    toggle.addEventListener('click', function () {
      const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
      root.dataset.theme = next;
      try { localStorage.setItem('mb-theme', next); } catch (e) { /* storage disabled */ }
      syncToggle();
    });
  }

  /* ---------- Toast auto dismiss ---------- */
  document.querySelectorAll('.toast').forEach(function (toast) {
    window.setTimeout(function () {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(30px)';
      window.setTimeout(function () { toast.remove(); }, 300);
    }, 5000);
  });

  /* ---------- Mobile navigation ---------- */
  const burger = document.getElementById('navBurger');
  const navLinks = document.getElementById('navLinks');
  if (burger && navLinks) {
    burger.addEventListener('click', function () {
      const open = navLinks.classList.toggle('open');
      burger.setAttribute('aria-expanded', String(open));
    });
    navLinks.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () {
        navLinks.classList.remove('open');
        burger.setAttribute('aria-expanded', 'false');
      });
    });
  }

  /* ---------- Instant mentor filter (directory page) ---------- */
  const instantFilter = document.getElementById('instantFilter');
  if (instantFilter) {
    const cards = Array.prototype.slice.call(document.querySelectorAll('#mentorGrid .mentor-card'));
    const count = document.getElementById('resultCount');
    instantFilter.addEventListener('input', function () {
      const term = instantFilter.value.trim().toLowerCase();
      let visible = 0;
      cards.forEach(function (card) {
        const haystack = (card.dataset.search || '') + ' ' + (card.dataset.category || '');
        const match = !term || haystack.indexOf(term) !== -1;
        card.hidden = !match;
        if (match) visible++;
      });
      if (count) count.textContent = String(visible);
    });
  }

  /* ---------- Magnetic spotlight on bento / feature cards ---------- */
  document.querySelectorAll('.magnetic').forEach(function (card) {
    card.addEventListener('mousemove', function (event) {
      const rect = card.getBoundingClientRect();
      card.style.setProperty('--mx', ((event.clientX - rect.left) / rect.width * 100).toFixed(1) + '%');
      card.style.setProperty('--my', ((event.clientY - rect.top) / rect.height * 100).toFixed(1) + '%');
    });
  });

  /* ---------- Count-up stats ---------- */
  const counters = document.querySelectorAll('.counter[data-target]');
  if (counters.length && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        const el = entry.target;
        const target = Number(el.dataset.target) || 0;
        const suffix = el.textContent.trim().slice(-1);
        const duration = 1100;
        const start = performance.now();
        function frame(now) {
          const progress = Math.min((now - start) / duration, 1);
          const eased = 1 - Math.pow(1 - progress, 3);
          el.textContent = Math.round(target * eased).toLocaleString('en-IN') + (/[+%]/.test(suffix) ? suffix : '+');
          if (progress < 1) requestAnimationFrame(frame);
        }
        requestAnimationFrame(frame);
        observer.unobserve(el);
      });
    }, { threshold: .4 });
    counters.forEach(function (c) { observer.observe(c); });
  }

  /* ---------- Signup role cards ---------- */
  const roleInput = document.getElementById('roleInput');
  const mentorFields = document.getElementById('mentorFields');
  document.querySelectorAll('input[name="rolePicker"]').forEach(function (radio) {
    radio.addEventListener('change', function () {
      if (roleInput) roleInput.value = radio.value;
      document.querySelectorAll('.role-option').forEach(function (opt) {
        opt.classList.toggle('selected', opt.contains(radio));
      });
      if (mentorFields) mentorFields.hidden = radio.value !== 'mentor';
    });
  });

  /* ---------- Avatar fallback: Unsplash photo -> DiceBear generated avatar ---------- */
  document.querySelectorAll('img[data-fallback-seed]').forEach(function (img) {
    img.addEventListener('error', function () {
      if (img.dataset.fallbackUsed) return;
      img.dataset.fallbackUsed = '1';
      const seed = encodeURIComponent(img.dataset.fallbackSeed || 'mentor');
      img.src = 'https://api.dicebear.com/9.x/notionists/svg?seed=' + seed + '&backgroundColor=bef264,064e3b';
    });
  });
})();
