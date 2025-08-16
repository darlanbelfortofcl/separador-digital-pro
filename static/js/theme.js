(function(){
  const root = document.documentElement;
  const getSaved = () => localStorage.getItem('theme') || document.cookie.replace(/(?:(?:^|.*;\s*)theme\s*\=\s*([^;]*).*$)|^.*$/, '$1');
  const apply = (t) => { root.setAttribute('data-theme', t); localStorage.setItem('theme', t); document.cookie='theme='+t+';path=/;max-age=31536000'; };
  const init = () => {
    const saved = getSaved();
    if(saved) apply(saved);
    const btn = document.getElementById('theme-toggle');
    const setIcon = () => btn.textContent = (root.getAttribute('data-theme') === 'light') ? '🌙' : '☀️';
    setIcon();
    btn.addEventListener('click', ()=>{ apply(root.getAttribute('data-theme')==='light'?'dark':'light'); setIcon(); });
  };
  window.addEventListener('DOMContentLoaded', init);
})();