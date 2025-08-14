
function $(s){return document.querySelector(s)}
const bar = $("#bar");
const statusEl = $("#status");
const loading = $("#loading");
const dl = $("#download");

$("#form-dividir").addEventListener("submit", async (e)=>{
  e.preventDefault();
  bar.style.width = "0%"; bar.classList.remove("done","error");
  statusEl.textContent = "";
  dl.innerHTML = "";
  loading.hidden = false;

  const fd = new FormData();
  const file = $("#fileSplit").files[0];
  if(!file){ statusEl.textContent = "Selecione um PDF."; loading.hidden = true; return; }
  fd.append("arquivo_pdf", file);
  fd.append("qualidade", $("#qualidade").value);

  let resp;
  try{
    resp = await fetch("/process", { method: "POST", body: fd });
  }catch(err){
    statusEl.textContent = "Falha ao conectar ao servidor.";
    loading.hidden = true;
    bar.classList.add("error"); bar.style.width = "100%";
    return;
  }
  const data = await resp.json().catch(()=>({ok:false,error:"Erro inesperado"}));
  if(!data.ok){ statusEl.textContent = data.error || "Erro no envio."; loading.hidden = true; bar.classList.add("error"); bar.style.width = "100%"; return; }

  const es = new EventSource(`/stream?job=${data.job_id}`);
  es.onmessage = (ev)=>{
    try{
      const payload = JSON.parse(ev.data);
      if(payload.atual != null && payload.total){
        const pct = Math.max(0, Math.min(100, parseInt(payload.atual)));
        bar.style.width = pct + "%";
      }
      if(payload.msg) statusEl.textContent = payload.msg;
      if(payload.error){
        es.close();
        loading.hidden = true;
        bar.classList.add("error"); bar.style.width = "100%";
      }
      if(payload.download){
        const a = document.createElement("a");
        a.href = `/download?path=${encodeURIComponent(payload.download)}`;
        a.textContent = "Baixar ZIP";
        dl.appendChild(a);
      }
      if(payload.done){
        es.close();
        loading.hidden = true;
        bar.classList.add("done"); bar.style.width = "100%";
        if(!payload.download){ statusEl.textContent = "Concluído."; }
      }
    }catch(e){ /* ignora parse */ }
  };
  es.onerror = ()=>{
    statusEl.textContent = "Conexão de progresso interrompida.";
    loading.hidden = true;
  };
});
