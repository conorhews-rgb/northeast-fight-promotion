/* =========================================================
   NORTHEAST FIGHT PROMOTION site.js
   Motion and interaction. No dependencies.
   ========================================================= */
(function () {
  "use strict";

  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const $ = (s, c) => (c || document).querySelector(s);
  const $$ = (s, c) => Array.from((c || document).querySelectorAll(s));

  /* ---------------------------------------------------------
     0. Intro overlay
     Holds on the mark, then flies it onto the real hero logo. The page
     builds in underneath on the same frame the flight starts, so the
     site assembles around the mark instead of being uncovered behind
     it. CSS carries a no-JS fallback fade.
     --------------------------------------------------------- */
  const root = document.documentElement;
  const intro = $(".intro");

  // Reveals must not fire while the overlay is up, or the page has already
  // finished assembling by the time anyone can see it. Section 3 waits for
  // this, and built() is safe to call more than once.
  let builtFired = false;
  const built = () => {
    if (builtFired) return;
    builtFired = true;
    document.dispatchEvent(new CustomEvent("nfp:built"));
  };

  if (intro) {
    const introLogo = $(".intro-logo", intro);
    const heroLogo = $(".hero-media > img:not(.region)");
    const clearIntro = () => {
      // deliberately not is-built: its own timer clears it once the build-in
      // keyframes have finished, and this runs before they have
      root.classList.remove("is-booting", "intro-running");
      built();
      intro.remove();
    };

    if (reduced) {
      clearIntro();
    } else {
      intro.classList.add("intro--js");
      // whatever happens below, the overlay always goes away
      setTimeout(clearIntro, 6000);

      const settled = (p) => (p && p.then ? p.catch(() => {}) : Promise.resolve());
      const wait = (ms) => new Promise((r) => setTimeout(r, ms));

      // Gate on the mark itself only. Fonts are irrelevant here and waiting on
      // them leaves the viewer on a black screen for however long they take.
      // The race caps the wait so a slow image can never stall the intro.
      const marksReady = Promise.race([
        Promise.all([
          settled(introLogo.decode && introLogo.decode()),
          settled(heroLogo && heroLogo.decode && heroLogo.decode())
        ]),
        wait(1200)
      ]);

      Promise.all([
        marksReady,
        wait(300) // a minimum beat, so the mark never just flashes past
      ])
        .then(() => {
          intro.classList.add("is-showing");
          return wait(620);
        })
        .then(() => {
          // Measure against where the hero mark will END UP. The hero panel is
          // held at opacity 0 right now but is laid out, so the rect is real.
          if (heroLogo) {
            const a = introLogo.getBoundingClientRect();
            const b = heroLogo.getBoundingClientRect();
            if (a.width > 0 && b.width > 0) {
              const dx = b.left + b.width / 2 - (a.left + a.width / 2);
              const dy = b.top + b.height / 2 - (a.top + a.height / 2);
              introLogo.style.transform =
                "translate(" + dx.toFixed(1) + "px," + dy.toFixed(1) + "px) scale(" +
                (b.width / a.width).toFixed(4) + ")";
            }
          }
          // Same frame: the mark starts moving, the black ground starts
          // dissolving, and the page starts building in behind it.
          intro.classList.add("is-done");
          root.classList.remove("is-booting");
          root.classList.add("is-built");
          built();
          // The build-in keyframes use fill both, which pins elements at
          // opacity 0 until they run. Drop the class once they have finished
          // so the page can never depend on an animation to become visible.
          setTimeout(() => root.classList.remove("is-built"), 1400);
          return wait(1000); // the flight
        })
        .then(clearIntro); // hand the mark over to the real hero logo
    }
  } else {
    built();
  }

  /* ---------------------------------------------------------
     1. Header state and scroll progress
     --------------------------------------------------------- */
  const header = $(".site-header");
  const progress = $(".scroll-progress");

  function onScroll() {
    const y = window.scrollY;
    if (header) header.classList.toggle("is-stuck", y > 30);
    if (progress) {
      const max = document.documentElement.scrollHeight - window.innerHeight;
      progress.style.transform = "scaleX(" + (max > 0 ? y / max : 0) + ")";
    }
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ---------------------------------------------------------
     2. Mobile menu
     --------------------------------------------------------- */
  const burger = $(".burger");
  const drawer = $(".mobile-menu");
  if (burger && drawer) {
    const toggle = (open) => {
      burger.setAttribute("aria-expanded", String(open));
      drawer.classList.toggle("is-open", open);
      document.body.classList.toggle("menu-open", open);
    };
    burger.addEventListener("click", () =>
      toggle(burger.getAttribute("aria-expanded") !== "true")
    );
    $$("a", drawer).forEach((a) => a.addEventListener("click", () => toggle(false)));
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") toggle(false);
    });
  }

  /* ---------------------------------------------------------
     3. Scroll reveals
     --------------------------------------------------------- */
  const revealables = $$("[data-reveal]");
  if (revealables.length) {
    if (reduced || !("IntersectionObserver" in window)) {
      revealables.forEach((el) => el.classList.add("is-in"));
    } else {
      const io = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (!entry.isIntersecting) return;
            entry.target.classList.add("is-in");
            io.unobserve(entry.target);
          });
        },
        { threshold: 0.1, rootMargin: "0px 0px -6% 0px" }
      );
      const startObserving = () => {
        revealables.forEach((el) => {
          const delay = el.getAttribute("data-delay");
          if (delay) el.style.setProperty("--d", delay + "ms");
          io.observe(el);
        });
      };
      // Hold until the intro hands off, otherwise everything above the fold
      // reveals itself behind the overlay and the page is already finished
      // when it comes into view.
      if (builtFired) startObserving();
      else document.addEventListener("nfp:built", startObserving, { once: true });
    }
  }

  /* stagger the children of any [data-stagger] container */
  $$("[data-stagger]").forEach((group) => {
    const step = parseInt(group.getAttribute("data-stagger"), 10) || 80;
    Array.from(group.children).forEach((child, i) => {
      if (child.hasAttribute("data-reveal") && !child.hasAttribute("data-delay")) {
        child.style.setProperty("--d", i * step + "ms");
      }
    });
  });

  /* ---------------------------------------------------------
     4. Countdown clocks
     [data-countdown="2026-10-24T19:00:00-04:00"]
     --------------------------------------------------------- */
  $$("[data-countdown]").forEach((root) => {
    const target = new Date(root.getAttribute("data-countdown")).getTime();
    const out = {
      d: $('[data-cd="d"]', root),
      h: $('[data-cd="h"]', root),
      m: $('[data-cd="m"]', root),
      s: $('[data-cd="s"]', root)
    };
    const pad = (n) => String(Math.max(0, n)).padStart(2, "0");

    function tick() {
      const diff = target - Date.now();
      const total = diff > 0 ? Math.floor(diff / 1000) : 0;
      if (out.d) out.d.textContent = pad(Math.floor(total / 86400));
      if (out.h) out.h.textContent = pad(Math.floor((total % 86400) / 3600));
      if (out.m) out.m.textContent = pad(Math.floor((total % 3600) / 60));
      if (out.s) out.s.textContent = pad(total % 60);
    }
    tick();
    setInterval(tick, 1000);
  });

  /* ---------------------------------------------------------
     5. Count-up numbers [data-count="6"]
     --------------------------------------------------------- */
  const counters = $$("[data-count]");
  if (counters.length) {
    const run = (el) => {
      const end = parseFloat(el.getAttribute("data-count"));
      const suffix = el.getAttribute("data-suffix") || "";
      if (reduced) {
        el.textContent = end + suffix;
        return;
      }
      const dur = 1200;
      const t0 = performance.now();
      const step = (t) => {
        const p = Math.min(1, (t - t0) / dur);
        el.textContent = Math.round(end * (1 - Math.pow(1 - p, 3))) + suffix;
        if (p < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    };
    if ("IntersectionObserver" in window) {
      const cio = new IntersectionObserver(
        (entries) => {
          entries.forEach((e) => {
            if (!e.isIntersecting) return;
            run(e.target);
            cio.unobserve(e.target);
          });
        },
        { threshold: 0.5 }
      );
      counters.forEach((el) => cio.observe(el));
    } else {
      counters.forEach(run);
    }
  }

  /* ---------------------------------------------------------
     6. Parallax [data-parallax="0.1"]
     --------------------------------------------------------- */
  const parallax = $$("[data-parallax]");
  if (parallax.length && !reduced) {
    let ticking = false;
    const update = () => {
      const vh = window.innerHeight;
      parallax.forEach((el) => {
        const rect = el.getBoundingClientRect();
        if (rect.bottom < -200 || rect.top > vh + 200) return;
        const speed = parseFloat(el.getAttribute("data-parallax")) || 0.1;
        const offset = (rect.top + rect.height / 2 - vh / 2) * speed;
        const base = el.getAttribute("data-parallax-base") || "";
        el.style.transform = base + " translate3d(0," + (-offset).toFixed(2) + "px,0)";
      });
      ticking = false;
    };
    window.addEventListener(
      "scroll",
      () => {
        if (!ticking) {
          ticking = true;
          requestAnimationFrame(update);
        }
      },
      { passive: true }
    );
    window.addEventListener("resize", update);
    update();
  }

  /* ---------------------------------------------------------
     7. Tab switchers (Upcoming / Past on the events page)
     --------------------------------------------------------- */
  $$("[data-tabs]").forEach((group) => {
    const buttons = $$("[data-tab]", group);
    buttons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const name = btn.getAttribute("data-tab");
        buttons.forEach((b) => b.setAttribute("aria-selected", String(b === btn)));
        $$("[data-panel]").forEach((panel) => {
          panel.hidden = panel.getAttribute("data-panel") !== name;
        });
      });
    });
  });

  /* ---------------------------------------------------------
     8. Accordions
     --------------------------------------------------------- */
  $$(".acc-item").forEach((item) => {
    const q = $(".acc-q", item);
    const a = $(".acc-a", item);
    if (!q || !a) return;
    q.setAttribute("aria-expanded", "false");
    q.addEventListener("click", () => {
      const open = item.classList.toggle("is-open");
      q.setAttribute("aria-expanded", String(open));
      a.style.maxHeight = open ? a.scrollHeight + "px" : "0px";
    });
  });

  /* ---------------------------------------------------------
     9. Forms
     There is no backend. Submitting opens a pre-filled email
     so the site works from day one. To move to a real handler
     later, swap this block for a fetch() POST.
     --------------------------------------------------------- */
  const INBOX =
    document.documentElement.getAttribute("data-inbox") ||
    "info@northeastfightpromotion.com";

  $$("form[data-mailto]").forEach((form) => {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const subject = form.getAttribute("data-subject") || "Website enquiry";
      const lines = [];
      new FormData(form).forEach((value, key) => {
        if (String(value).trim()) {
          lines.push(key.replace(/_/g, " ").toUpperCase() + ": " + value);
        }
      });
      const body = lines.join("\n") + "\n\nSent from northeastfightpromotion.com";
      const success = $(".form-success", form);
      if (success) success.classList.add("is-on");
      window.location.href =
        "mailto:" + INBOX +
        "?subject=" + encodeURIComponent(subject) +
        "&body=" + encodeURIComponent(body);
      form.reset();
    });
  });

  /* ---------------------------------------------------------
     10. Year stamp
     --------------------------------------------------------- */
  $$("[data-year]").forEach((el) => {
    el.textContent = new Date().getFullYear();
  });
})();
