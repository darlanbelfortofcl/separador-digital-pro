async function postForm(url, data) {
  const res = await fetch(url, { method:"POST", body: data });
  if(!res.ok) throw new Error("Falha ao enviar");
  return res.json();
}
function el(q){return document.querySelector(q)}
function createConfetti(){
  const root=document.createElement("div"); root.className="confetti"; document.body.appendChild(root);
  const colors=["#22c55e","#06b6d4","#fde047","#f472b6","#60a5fa"];
  for(let i=0;i<80;i++){
    const s=document.createElement("span");
    s.style.left = Math.random()*100+"%";
    s.style.top = "-10px";
    s.style.color = colors[Math.floor(Math.random()*colors.length)];
    s.style.transform = `translateY(0) rotate(${Math.random()*360}deg)`;
    s.style.animationDelay = (Math.random()*0.6)+"s";
    root.appendChild(s);
  }
  setTimeout(()=>root.remove(), 2200);
}
window.addEventListener("DOMContentLoaded", ()=>{
  const form = el("#pdf-form");
  const bar = el(".bar");
  const status = el("#status");
  const thumbs = el("#thumbs");
  const download = el("#download");
  form?.addEventListener("submit", async (ev)=>{
    ev.preventDefault();
    thumbs.innerHTML = ""; download.innerHTML="";
    const fd = new FormData(form);
    bar.style.width = "0%"; status.textContent = "Enviando…";
    try{
      const data = await postForm("/processar", fd);
      if(!data.ok) throw new Error(data.msg||"Erro desconhecido");
      const jobId = data.job_id;
      const sse = new EventSource(`/eventos/${jobId}`);
      sse.onmessage = (e)=>{
        const payload = JSON.parse(e.data);
        if(payload.percent!==undefined){
          bar.style.width = payload.percent + "%";
        }
        if(payload.status){ status.textContent = payload.status; }
        if(payload.download){
          sse.close();
          createConfetti();
          const a = document.createElement("a");
          a.href = payload.download;
          a.className = "btn";
          a.textContent = "Baixar ZIP";
          download.appendChild(a);
          // gerar thumbs "leves": 12 primeiras páginas (embed escalado)
          const range = (fd.get("paginas")||"").trim();
          const total = 200; // limite de tentativas de preview
          const chosen = [];
          // tenta adivinhar páginas do range ou cria sequência
          if(range){
            range.split(",").forEach(part=>{
              if(part.includes("-")){
                const [a,b]=part.split("-").map(x=>parseInt(x,10));
                if(!isNaN(a)&&!isNaN(b)){
                  const s=Math.min(a,b), e=Math.max(a,b);
                  for(let p=s; p<=e && chosen.length<12; p++) chosen.push(p);
                }
              }else{
                const p=parseInt(part,10); if(!isNaN(p) && chosen.length<12) chosen.push(p);
              }
            });
          }
          if(chosen.length===0){ for(let i=1;i<=12;i++) chosen.push(i); }
          thumbs.innerHTML = "";
          chosen.forEach(p=>{
            const div=document.createElement("div"); div.className="thumb";
            const tag=document.createElement("div"); tag.className="tag"; tag.textContent="Página "+p;
            const emb=document.createElement("embed"); emb.src=`/preview/${jobId}/${p}`; emb.type="application/pdf";
            div.appendChild(emb); div.appendChild(tag); thumbs.appendChild(div);
          });
        }
      };
      sse.onerror = ()=>{ status.textContent = "Conexão com servidor de eventos perdida."; sse.close(); };
    }catch(err){
      status.textContent = err.message;
    }
  });
});
