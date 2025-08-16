document.addEventListener('DOMContentLoaded', () => {
  const forms = ['form-convert','form-split','form-merge']
    .map(id => document.getElementById(id))
    .filter(Boolean);

  forms.forEach(form => {
    form.addEventListener('submit', (e) => {
      // deixamos o submit padrão acontecer para download direto
      const btn = form.querySelector('button');
      btn.disabled = true;
      const old = btn.textContent;
      btn.textContent = 'Processando...';
      setTimeout(()=>{ btn.disabled=false; btn.textContent = old; }, 6000);
    });
  });
});
