(function(){
  const key="sdp-theme"; const root=document.documentElement;
  function apply(t){ root.setAttribute("data-theme", t); localStorage.setItem(key,t); }
  const saved=localStorage.getItem(key); if(saved){ apply(saved); }
  const btn=document.getElementById("themeToggle");
  if(btn){ btn.addEventListener("click", ()=>{ apply(root.getAttribute("data-theme")==="dark"?"light":"dark"); }); }
})();
