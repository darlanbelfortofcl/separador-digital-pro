
const $ = (sel)=>document.querySelector(sel);
const $$ = (sel)=>document.querySelectorAll(sel);

const themeToggle = $("#themeToggle");
const dropzone = $("#dropzone");
const fileInput = $("#fileInput");
const fileList = $("#fileList");
const startBtn = $("#startBtn");
const clearBtn = $("#clearBtn");
const uploadProgress = $("#uploadProgress");
const barFill = $("#barFill");
const progressText = $("#progressText");
const processing = $("#processing");
const statusText = $("#statusText");
const results = $("#results");
const zipLink = $("#zipLink");
const filesOut = $("#filesOut");
const feedback = $("#feedback");

let files = [];

// ---- THEME ----
(function initTheme(){
  const saved = localStorage.getItem("theme") || "dark";
  if(saved === "light") document.body.classList.add("light");
  themeToggle.textContent = saved === "light" ? "☀️" : "🌙";
})();

themeToggle.addEventListener("click", ()=>{
  const isLight = document.body.classList.toggle("light");
  localStorage.setItem("theme", isLight ? "light" : "dark");
  themeToggle.textContent = isLight ? "☀️" : "🌙";
});

// ---- FILES ----
dropzone.addEventListener("dragover", (e)=>{ e.preventDefault(); dropzone.style.transform = "scale(1.01)"; });
dropzone.addEventListener("dragleave", ()=>{ dropzone.style.transform = "scale(1)"; });
dropzone.addEventListener("drop", (e)=>{
  e.preventDefault(); dropzone.style.transform = "scale(1)";
  const dropped = Array.from(e.dataTransfer.files).filter(f => f.type === "application/pdf" || f.name.toLowerCase().endsWith(".pdf"));
  if (!dropped.length){ toastError("Apenas PDFs são permitidos."); return; }
  files = files.concat(dropped);
  renderList();
});
dropzone.addEventListener("click", ()=> fileInput.click());
fileInput.addEventListener("change", ()=>{
  const picked = Array.from(fileInput.files).filter(f => f.type === "application/pdf" || f.name.toLowerCase().endsWith(".pdf"));
  if (!picked.length){ toastError("Apenas PDFs são permitidos."); return; }
  files = files.concat(picked);
  renderList();
});

clearBtn.addEventListener("click", ()=>{
  files = [];
  renderList();
  hide(results, processing, feedback);
  hide(uploadProgress);
  barFill.style.width = "0%";
  progressText.textContent = "Enviando 0%";
});

function renderList(){
  startBtn.disabled = files.length === 0;
  if(!files.length){ fileList.innerHTML = ""; return; }
  fileList.innerHTML = files.map(f => `
    <div class="item">
      <div class="name">📄 ${f.name}</div>
      <div class="meta">${(f.size/1024/1024).toFixed(2)} MB</div>
    </div>
  `).join("");
}

// ---- HELPERS ----
function show(...els){ els.forEach(el=> el.hidden = false); }
function hide(...els){ els.forEach(el=> el.hidden = true); }
function toastError(msg){
  feedback.textContent = msg;
  feedback.hidden = false;
  setTimeout(()=> feedback.hidden = true, 6000);
}

// ---- UPLOAD & PROCESS ----
startBtn.addEventListener("click", async ()=>{
  if(!files.length) return;
  feedback.hidden = true;
  results.hidden = true;
  processing.hidden = true;
  show(uploadProgress);
  startBtn.disabled = true;

  barFill.style.width = "0%";
  progressText.textContent = "Enviando 0%";

  try{
    const fd = new FormData();
    files.forEach(f => fd.append("files", f));

    const xhr = new XMLHttpRequest();
    const promise = new Promise((resolve, reject)=>{
      xhr.open("POST", "/upload");
      xhr.upload.onprogress = (e)=>{
        if(e.lengthComputable){
          const pct = Math.round((e.loaded / e.total) * 100);
          barFill.style.width = pct + "%";
          progressText.textContent = "Enviando " + pct + "%";
        }
      };
      xhr.onload = ()=>{
        if(xhr.status >= 200 && xhr.status < 300) resolve(JSON.parse(xhr.responseText));
        else reject(new Error("Falha no upload (" + xhr.status + ")"));
      };
      xhr.onerror = ()=> reject(new Error("Erro de rede no upload"));
      xhr.send(fd);
    });

    const data = await promise;
    hide(uploadProgress);
    if(!data.job_id) throw new Error("job_id inválido");

    show(processing);
    statusText.textContent = "Processando...";

    await pollStatus(data.job_id, 180); // timeout de 180s
  }catch(err){
    hide(uploadProgress, processing);
    startBtn.disabled = false;
    toastError("Erro: " + err.message);
  }
});

async function pollStatus(jobId, timeoutSec=180){
  const started = Date.now();
  const delay = (ms)=> new Promise(r=> setTimeout(r, ms));
  while(true){
    if((Date.now()-started)/1000 > timeoutSec){
      hide(processing);
      startBtn.disabled = false;
      toastError("Tempo esgotado ao processar. Tente novamente.");
      return;
    }
    try{
      const r = await fetch(`/status/${jobId}`, { cache:"no-store" });
      if(!r.ok){
        await delay(1200);
        continue;
      }
      const s = await r.json();
      if(s.error){
        hide(processing);
        startBtn.disabled = false;
        toastError(s.error);
        return;
      }
      statusText.textContent = `Status: ${s.status} — ${s.progress || 0}%`;
      if(s.status === "finished"){
        hide(processing);
        show(results);
        zipLink.href = `/download/${jobId}`; // Baixar Todos (ZIP)
        await loadList(jobId);               // Baixar individuais
        startBtn.disabled = false;
        return;
      }
      if(s.status === "failed"){
        hide(processing);
        startBtn.disabled = false;
        toastError("O processamento falhou.");
        return;
      }
    }catch(e){
      // falha intermitente: espera e tenta de novo
    }
    await delay(1200);
  }
}

async function loadList(jobId){
  try{
    const r = await fetch("/list/" + jobId, { cache:"no-store" });
    const d = await r.json();
    if(!d.files) return;
    filesOut.innerHTML = d.files.map(name => `
      <div class="file-out">
        <div class="name">📄 ${name}</div>
        <a class="btn ghost" href="/download/${jobId}/${encodeURIComponent(name)}" download>Baixar</a>
      </div>
    `).join("");
  }catch(_){ /* ignore */ }
}
