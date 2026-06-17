(function () {
  var links = Array.prototype.slice.call(document.querySelectorAll(".toc a"));
  if (!links.length) return;
  var sections = links.map(function (a) {
    return document.querySelector(a.getAttribute("href"));
  }).filter(Boolean);

  function onScroll() {
    var y = window.scrollY + 110;
    var current = sections[0];
    sections.forEach(function (sec) {
      if (sec.offsetTop <= y) current = sec;
    });
    links.forEach(function (a) {
      a.classList.toggle("active", a.getAttribute("href") === "#" + current.id);
    });
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
})();
