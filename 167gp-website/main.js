/* =============================================
   167 General Partners — main.js
   ============================================= */

// ---------- Scroll-aware nav ----------
const nav = document.getElementById('nav');

const onScroll = () => {
  nav.classList.toggle('scrolled', window.scrollY > 40);
};
window.addEventListener('scroll', onScroll, { passive: true });
onScroll(); // run once on load

// ---------- Mobile nav toggle ----------
const toggle = nav.querySelector('.nav-toggle');
const navLinks = nav.querySelector('.nav-links');

toggle.addEventListener('click', () => {
  const isOpen = nav.classList.toggle('open');
  toggle.setAttribute('aria-expanded', String(isOpen));
  document.body.style.overflow = isOpen ? 'hidden' : '';
});

// Close mobile nav when a link is clicked
navLinks.querySelectorAll('a').forEach(link => {
  link.addEventListener('click', () => {
    nav.classList.remove('open');
    toggle.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
  });
});

// ---------- Footer year ----------
const yearEl = document.getElementById('year');
if (yearEl) yearEl.textContent = new Date().getFullYear();

// ---------- Contact form ----------
const form = document.getElementById('contact-form');
const successEl = document.getElementById('form-success');

if (form) {
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    successEl.textContent = '';

    // Basic client-side validation
    let valid = true;
    ['name', 'email', 'message'].forEach(fieldId => {
      const el = document.getElementById(fieldId);
      const empty = !el.value.trim();
      const badEmail = fieldId === 'email' && el.value && !isValidEmail(el.value);
      el.classList.toggle('error', empty || badEmail);
      if (empty || badEmail) valid = false;
    });

    if (!valid) return;

    // Simulate form submission (replace with your actual endpoint)
    const btn = form.querySelector('button[type="submit"]');
    btn.textContent = 'Sending…';
    btn.disabled = true;

    setTimeout(() => {
      btn.textContent = 'Send Message';
      btn.disabled = false;
      form.reset();
      successEl.textContent = "Thanks — we'll be in touch soon.";
    }, 1200);
  });

  // Clear error state on input
  form.querySelectorAll('input, textarea, select').forEach(el => {
    el.addEventListener('input', () => el.classList.remove('error'));
  });
}

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// ---------- Intersection observer: fade-in sections ----------
const IO = new IntersectionObserver(
  (entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        IO.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.08 }
);

document.querySelectorAll('.thesis-card, .team-card, .stat').forEach(el => {
  el.classList.add('fade-up');
  IO.observe(el);
});
