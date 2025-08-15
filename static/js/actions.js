(function(){
  async function postForm(url, form){
    const fd=new FormData();
    const input=form.querySelector('.upload-area input[type=file]');
    if(input && input.files.length){ for(const f of input.files){ fd.append('arquivos', f);} }
    const r=await fetch(url,{method:'POST', body:fd}); return r.json();
  }
  async function poll(taskId, onTick, onDone, onError){
    const loop=async()=>{
      try{
        const r=await fetch(`/api/status/${taskId}`); const j=await r.json();
        if(!j.ok){ onError(j.error||'Erro'); return; }
        if(['PENDING','RECEIVED','STARTED'].includes(j.state)){ onTick && onTick(); setTimeout(loop,800); }
        else if(j.state==='SUCCESS'){ onDone && onDone(j.result); }
        else if(j.state==='FAILURE'){ onError && onError(j.error||'Falha'); }
        else{ setTimeout(loop,1000); }
      }catch(e){ onError && onError(e.message); }
    }; loop();
  }
  function wire(form){
    const btn=form.querySelector('button[data-action]');
    const bar=form.querySelector('.progress .bar');
    const result=form.querySelector('.result');
    btn.addEventListener('click', async (e)=>{
      e.preventDefault(); result.innerHTML=''; bar.style.width='0%'; btn.disabled=true;
      const map={split:'/api/split',merge:'/api/merge',compress:'/api/compress','pdf-to-docx':'/api/pdf-to-docx'};
      try{
        const j=await postForm(map[btn.dataset.action], form);
        if(!j.ok) throw new Error(j.error||'Erro');
        if(j.path){ // synchronous fallback
          bar.style.width='100%';
          const a=document.createElement('a'); a.href='/download?path='+encodeURIComponent(j.path); a.className='btn'; a.textContent='Baixar'; result.appendChild(a); btn.disabled=false; return;
        }
        let pct=0;
        poll(j.task_id, ()=>{ pct=Math.min(100,pct+8); bar.style.width=pct+'%'; },
          (path)=>{ bar.style.width='100%'; const a=document.createElement('a'); a.href='/download?path='+encodeURIComponent(path); a.className='btn'; a.textContent='Baixar'; result.appendChild(a); btn.disabled=false; },
          (err)=>{ result.textContent='Erro: '+err; btn.disabled=false; }
        );
      }catch(e){ result.textContent='Erro: '+e.message; btn.disabled=false; }
    });
  }
  document.addEventListener('DOMContentLoaded',()=>{
    document.querySelectorAll('form.upload-form').forEach(wire);
  });
})();
