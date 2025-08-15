(function(){
  async function postForm(url, form){
    const fd=new FormData();
    const input=form.querySelector('.upload-area input[type=file]');
    if(input && input.files.length){
      for(const f of input.files){ fd.append('arquivos', f); }
    }
    const ocr=form.querySelector('input[name=ocr]');
    if(ocr) fd.append('ocr', ocr.checked ? 'on' : '');
    const resp=await fetch(url,{method:'POST', body: fd});
    return resp.json();
  }
  async function poll(taskId, onProgress, onDone, onError){
    const tick=async()=>{
      try{
        const r=await fetch(`/api/status/${taskId}`);
        const j=await r.json();
        if(!j.ok){ onError(j.error||'Erro'); return; }
        if(j.state==='PENDING' || j.state==='RECEIVED' || j.state==='STARTED'){
          onProgress && onProgress();
          setTimeout(tick, 800);
        }else if(j.state==='SUCCESS'){
          onDone && onDone(j.result);
        }else if(j.state==='FAILURE'){
          onError && onError(j.error || 'Falha no processamento');
        }else{
          setTimeout(tick, 1000);
        }
      }catch(e){ onError && onError(e.message); }
    };
    tick();
  }
  function wireAction(form, action){
    const btn=form.querySelector('button[data-action]');
    const bar=form.querySelector('.progress .bar');
    const result=form.querySelector('.result');
    const feedback=form.querySelector('.feedback');
    btn.addEventListener('click', async (e)=>{
      e.preventDefault();
      result.innerHTML=''; feedback && (feedback.textContent='Enviando…');
      bar.style.width='0%'; btn.disabled=true;
      try{
        const endpoint={
          split:'/api/split',
          merge:'/api/merge',
          compress:'/api/compress',
          'pdf-to-docx':'/api/pdf-to-docx'
        }[action];
        const j=await postForm(endpoint, form);
        if(!j.ok){ throw new Error(j.error||'Erro'); }
        feedback && (feedback.textContent='Processando…');
        let pct=0;
        poll(j.task_id,
          ()=>{ pct=Math.min(100, pct+8); bar.style.width=pct+'%'; },
          (path)=>{ bar.style.width='100%'; feedback && (feedback.textContent='Concluído'); 
            const a=document.createElement('a'); a.href='/download?path='+encodeURIComponent(path); a.textContent='Baixar arquivo'; a.className='btn'; a.style.background='var(--highlight)'; a.style.textDecoration='none';
            a.style.animation='pulse 1s infinite'; result.appendChild(a); btn.disabled=false; },
          (err)=>{ feedback && (feedback.textContent='Erro: '+err); btn.disabled=false; }
        );
      }catch(err){
        feedback && (feedback.textContent='Erro: '+err.message);
        btn.disabled=false;
      }
    });
  }
  document.addEventListener('DOMContentLoaded',()=>{
    document.querySelectorAll('form.upload-form').forEach(form=>{
      const btn=form.querySelector('button[data-action]');
      if(!btn) return;
      wireAction(form, btn.getAttribute('data-action'));
    });
  });
})();
