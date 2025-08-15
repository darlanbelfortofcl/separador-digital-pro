(function(){
  const key='pref-theme';
  const root=document.documentElement;
  const btn=document.getElementById('theme-toggle');
  function apply(theme){
    root.setAttribute('data-theme', theme);
    localStorage.setItem(key, theme);
  }
  const saved=localStorage.getItem(key);
  if(saved){ apply(saved); }
  if(btn){
    btn.addEventListener('click',()=>{
      const current=root.getAttribute('data-theme')||'light';
      apply(current==='light'?'dark':'light');
    });
  }
})();
