(function () {
  const header = document.getElementById("header");

  const root = document.documentElement;
  const maxScroll = 100; 

  let latestKnownScrollY = 0;
  let ticking = false;

  function clamp(v, a, b) {
    return Math.max(a, Math.min(b, v));
  }

  function update() {
    ticking = false;
    const scrollY = latestKnownScrollY;
    // progress 0..1
    const p = clamp(scrollY / maxScroll, 0, 1);
    // write as number with 3 decimals for CSS variable
    root.style.setProperty("--s", p.toFixed(3));

    // Add tiny class to control box-shadow/border only when scrolled a bit
    if (p > 0.4) {
      header.classList.add("scrolled");
    } else {
      header.classList.remove("scrolled");
    }
  }

  function onScroll() {
    latestKnownScrollY = window.scrollY || window.pageYOffset;
    if (!ticking) {
      window.requestAnimationFrame(update);
      ticking = true;
    }
  }


  if (header!==null) {
  window.addEventListener("scroll", onScroll, { passive: true });

  // Initialize (in case page is loaded scrolled)
  latestKnownScrollY = window.scrollY || window.pageYOffset;

    update();
  }

})();
