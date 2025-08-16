(function(){
  const root = document.documentElement;
  const saved = localStorage.getItem('theme') || document.cookie.replace(/(?:(?:^|.*;\s*)theme\s*\=\s*([^;]*).*$)|^.*$/, '$1');
  if(saved){ root.setAttribute('data-theme', saved); }
  window.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('theme-toggle');
    const isLight = root.getAttribute('data-theme') === 'light';
    btn.textContent = isLight ? '🌙' : '☀️';
    btn.addEventListener('click', () => {
      const cur = root.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
      root.setAttribute('data-theme', cur);
      localStorage.setItem('theme', cur);
      document.cookie = 'theme=' + cur + ';path=/;max-age=31536000';
      btn.textContent = cur === 'light' ? '🌙' : '☀️';
    });
  });
})();
