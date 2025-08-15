
(function(){
  const layer = document.querySelector('.mouse-layer');
  if(!layer) return;
  window.addEventListener('mousemove', (e)=>{
    const d = document.createElement('div');
    d.className = 'dot';
    d.style.left = e.clientX + 'px';
    d.style.top = e.clientY + 'px';
    layer.appendChild(d);
    setTimeout(()=> d.remove(), 800);
  }, {passive:true});
})();
