/*
 * ═══════════════════════════════════════════════════════════════
 *  Emirates NBD — Design System
 *  Consolidated JavaScript Utilities for Component Library
 *  Version: 1.0.0
 * ═══════════════════════════════════════════════════════════════
 */


/* ── 1. SCROLL REVEAL ─────────────────────────────────────────── */
/*
 * Usage: Add class="reveal" to any element.
 * Optional delay: add class="delay-1" / "delay-2" / "delay-3"
 * Triggers fade-up animation when element enters the viewport.
 */
(function initReveal() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
        observer.unobserve(e.target);
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.reveal').forEach(el => observer.observe(el));

  // Also trigger for elements already in view on load
  setTimeout(() => {
    document.querySelectorAll('.reveal').forEach(el => {
      if (el.getBoundingClientRect().top < window.innerHeight) {
        el.classList.add('visible');
      }
    });
  }, 200);
})();


/* ── 2. COUNTER ANIMATION ─────────────────────────────────────── */
/*
 * Usage: <span class="counter" data-end="200">0</span>
 * Optional decimals: data-decimals="1" → animates to e.g. 99.4
 * Triggers automatically when .counter enters the viewport.
 */
function animateCounter(el) {
  if (el._started) return;
  el._started = true;

  const end      = parseFloat(el.dataset.end || el.dataset.target || 0);
  const decimals = parseInt(el.dataset.decimals || 0);
  const duration = 2200;
  const start    = performance.now();

  function tick(now) {
    const progress = Math.min((now - start) / duration, 1);
    const eased    = 1 - Math.pow(1 - progress, 3); // ease-out cubic
    const value    = end * eased;
    el.textContent = decimals > 0 ? value.toFixed(decimals) : Math.round(value);
    if (progress < 1) requestAnimationFrame(tick);
    else el.textContent = decimals > 0 ? end.toFixed(decimals) : end;
  }

  requestAnimationFrame(tick);
}

(function initCounters() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.querySelectorAll('.counter').forEach(animateCounter);
        observer.unobserve(e.target);
      }
    });
  }, { threshold: 0.2 });

  // Observe parent reveal elements
  document.querySelectorAll('.reveal').forEach(el => observer.observe(el));

  // Also observe standalone counters
  document.querySelectorAll('.counter').forEach(el => {
    observer.observe(el.closest('.reveal') || el);
  });
})();


/* ── 3. AUTO-PROGRESS TABS ────────────────────────────────────── */
/*
 * Usage:
 *   ENBD.AutoProgress({
 *     tabs: [...],        // array of tab data objects
 *     interval: 4000,     // ms — auto-advance delay (desktop)
 *     mobileInterval: 10000, // ms — auto-advance delay (mobile/tablet)
 *     onTabChange: (tab, index) => {} // callback on tab change
 *   });
 */
const ENBD = window.ENBD || {};

ENBD.AutoProgress = function({ tabs = [], interval = 4000, mobileInterval = 10000, onTabChange } = {}) {
  let active = 0;
  let timer  = null;

  function getInterval() {
    return window.innerWidth < 1024 ? mobileInterval : interval;
  }

  function selectTab(idx) {
    active = (idx + tabs.length) % tabs.length;
    if (typeof onTabChange === 'function') onTabChange(tabs[active], active);
    startTimer();
  }

  function startTimer() {
    clearInterval(timer);
    timer = setInterval(() => selectTab(active + 1), getInterval());
  }

  function next() { selectTab(active + 1); }
  function prev() { selectTab(active - 1); }

  selectTab(0);

  return { next, prev, selectTab, getActive: () => active };
};


/* ── 4. IMAGE CROSSFADE SLIDER ────────────────────────────────── */
/*
 * Usage:
 *   ENBD.ImageSlider({
 *     slides: ['url1', 'url2'],
 *     container: document.getElementById('bg-container'),
 *     interval: 6500
 *   });
 */
ENBD.ImageSlider = function({ slides = [], container, interval = 6500 } = {}) {
  if (!container || slides.length === 0) return;

  let current = 0;

  function showSlide(idx) {
    const div = document.createElement('div');
    div.style.cssText = `
      position:absolute; inset:0; z-index:1;
      background: url('${slides[idx]}') center/cover no-repeat;
      animation: bgFade ${interval / 1000}s ease-in-out forwards;
    `;
    container.appendChild(div);
    setTimeout(() => div.remove(), interval);
  }

  showSlide(current);
  setInterval(() => {
    current = (current + 1) % slides.length;
    showSlide(current);
  }, interval);
};


/* ── 5. MARQUEE PAUSE ON HOVER ────────────────────────────────── */
/*
 * Usage: Add class="marquee-group" to the marquee wrapper.
 * Add class="marquee-inner" to the scrolling track.
 * Automatically pauses animation on hover.
 */
(function initMarquee() {
  document.querySelectorAll('.marquee-group').forEach(group => {
    group.addEventListener('mouseenter', () => {
      group.querySelectorAll('.marquee-inner').forEach(el => {
        el.style.animationPlayState = 'paused';
      });
    });
    group.addEventListener('mouseleave', () => {
      group.querySelectorAll('.marquee-inner').forEach(el => {
        el.style.animationPlayState = 'running';
      });
    });
  });
})();


/* ── 6. BREAKPOINT UTILITY ────────────────────────────────────── */
/*
 * Usage:
 *   ENBD.breakpoint()         → 'mobile' | 'tablet' | 'desktop'
 *   ENBD.isMobile()           → true if width < 768
 *   ENBD.isTablet()           → true if 768 ≤ width < 1024
 *   ENBD.isDesktop()          → true if width ≥ 1024
 */
ENBD.breakpoint = function() {
  const w = window.innerWidth;
  if (w < 768)  return 'mobile';
  if (w < 1024) return 'tablet';
  return 'desktop';
};
ENBD.isMobile  = () => window.innerWidth < 768;
ENBD.isTablet  = () => window.innerWidth >= 768 && window.innerWidth < 1024;
ENBD.isDesktop = () => window.innerWidth >= 1024;


/* ── 7. SMOOTH SCROLL TO SECTION ──────────────────────────────── */
/*
 * Usage: ENBD.scrollTo('#section-id');
 *   or   <a onclick="ENBD.scrollTo('#target')">Link</a>
 */
ENBD.scrollTo = function(selector, offset = 40) {
  const el = document.querySelector(selector);
  if (!el) return;
  const top = el.getBoundingClientRect().top + window.scrollY - offset;
  window.scrollTo({ top, behavior: 'smooth' });
};


/* ── 8. SCROLL PROGRESS INDICATOR ────────────────────────────── */
/*
 * Usage: ENBD.ScrollProgress({ el: document.getElementById('progress-bar') });
 * Updates width of el from 0→100% as user scrolls the page.
 */
ENBD.ScrollProgress = function({ el } = {}) {
  if (!el) return;
  window.addEventListener('scroll', () => {
    const scrolled  = window.scrollY;
    const maxScroll = document.body.scrollHeight - window.innerHeight;
    el.style.width  = `${(scrolled / maxScroll) * 100}%`;
  }, { passive: true });
};

window.ENBD = ENBD;
