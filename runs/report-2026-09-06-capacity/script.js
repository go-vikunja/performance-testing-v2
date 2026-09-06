  document.querySelectorAll('.chart').forEach(function (chart) {
    var tip = chart.querySelector('.tip');
    chart.querySelectorAll('[data-t]').forEach(function (el) {
      function show(e) {
        var r = chart.getBoundingClientRect();
        tip.textContent = el.getAttribute('data-t');
        tip.style.display = 'block';
        tip.style.left = (e.clientX - r.left) + 'px';
        tip.style.top = (e.clientY - r.top) + 'px';
      }
      el.addEventListener('mouseenter', show);
      el.addEventListener('mousemove', show);
      el.addEventListener('mouseleave', function () { tip.style.display = 'none'; });
    });
  });
