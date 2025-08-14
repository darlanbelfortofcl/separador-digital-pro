
function $(sel){return document.querySelector(sel)}
function addLog(el, msg){ el.innerHTML += `<div>${msg}</div>`; el.scrollTop = el.scrollHeight; }

// Tabs
document.querySelectorAll(".tab").forEach(btn=>{
  btn.addEventListener("click", ()=>{
    document.querySelectorAll(".tab").forEach(b=>b.classList.remove("active"));
    document.querySelectorAll(".panel").forEach(p=>p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(btn.dataset.tab).classList.add("active");
  });
});

// Converter
$("#form-converter").addEventListener("submit", async (e)=>{
  e.preventDefault();
  const log = $("#log-converter"); log.innerHTML = "";
  const fd = new FormData();
  const mode = $("#mode").value;
  const file = $("#fileConv").files[0];
  if(!file){ addLog(log, "Selecione um arquivo."); return; }
  fd.append("mode", mode);
  fd.append("arquivo", file); // <-- nome igual ao backend

  const resp = await fetch("/convert", { method: "POST", body: fd });
  const data = await resp.json();
  if(!data.ok){ addLog(log, data.error || "Erro no envio."); return; }

  const es = new EventSource(`/stream?job=${data.job_id}`);
  es.onmessage = (ev)=>{
    const payload = JSON.parse(ev.data);
    if(payload.msg) addLog(log, payload.msg);
    if(payload.download){
      const a = document.createElement("a");
      a.href = `/download?path=${encodeURIComponent(payload.download)}`;
      a.textContent = "Baixar resultado";
      a.className = "download";
      log.appendChild(a);
    }
    if(payload.done){ es.close(); }
  };
});

// Dividir
$("#form-dividir").addEventListener("submit", async (e)=>{
  e.preventDefault();
  const log = $("#log-dividir"); log.innerHTML = "";
  const fd = new FormData();
  const file = $("#fileSplit").files[0];
  if(!file){ addLog(log, "Selecione um PDF."); return; }
  fd.append("arquivo_pdf", file); // <-- nome igual ao backend
  fd.append("qualidade", $("#qualidade").value);

  const resp = await fetch("/process", { method: "POST", body: fd });
  const data = await resp.json();
  if(!data.ok){ addLog(log, data.error || "Erro no envio."); return; }

  const es = new EventSource(`/stream?job=${data.job_id}`);
  es.onmessage = (ev)=>{
    const payload = JSON.parse(ev.data);
    if(payload.msg) addLog(log, payload.msg);
    if(payload.download){
      const a = document.createElement("a");
      a.href = `/download?path=${encodeURIComponent(payload.download)}`;
      a.textContent = "Baixar páginas (ZIP)";
      a.className = "download";
      log.appendChild(a);
    }
    if(payload.done){ es.close(); }
  };
});
