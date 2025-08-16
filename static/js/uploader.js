document.addEventListener('DOMContentLoaded', () => {
  function bindForm(id){
    const form = document.getElementById(id);
    if(!form) return;
    const input = form.querySelector('input[type=file]');
    const list = document.querySelector(`.filelist[data-for="${id}"]`);
    input.addEventListener('change', () => {
      if(!list) return;
      if(!input.files || !input.files.length){ list.textContent=''; return; }
      const names = Array.from(input.files).map(f => `• ${f.name}`).join('\n');
      list.textContent = names;
    });
    form.addEventListener('submit', () => {
      const btn = form.querySelector('button');
      if(btn){ const old = btn.textContent; btn.dataset.old=old; btn.disabled=true; btn.textContent='Processando...'; setTimeout(()=>{btn.disabled=false; btn.textContent=old;}, 7000); }
    });
  }
  ['form-convert','form-split','form-merge'].forEach(bindForm);
});