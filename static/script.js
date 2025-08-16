
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

// Theme
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

// Drag and drop
dropzone.addEventListener("dragover", (e)=>{ e.preventDefault(); dropzone.style.transform = "scale(1.01)"; });
dropzone.addEventListener("dragleave", ()=>{ dropzone.style.transform = "scale(1)"; });
dropzone.addEventListener("drop", (e)=>{
  e.preventDefault(); dropzone.style.transform = "scale(1)";
  const dropped = Array.from(e.dataTransfer.files).filter(f => f.type === "application/pdf" || f.name.toLowerCase().endsWith(".pdf"));
  files = files.concat(dropped);
  renderList();
});
dropzone.addEventListener("click", ()=> fileInput.click());
fileInput.addEventListener("change", ()=>{
  files = files.concat(Array.from(fileInput.files));
  renderList();
});

clearBtn.addEventListener("click", ()=>{
  files = [];
  renderList();
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

// Upload + process
startBtn.addEventListener("click", async ()=>{
  if(!files.length) return;
  feedback.hidden = true;
  results.hidden = true;
  processing.hidden = true;
  uploadProgress.hidden = false;
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
        else reject(new Error("Falha no upload"));
      };
      xhr.onerror = ()=> reject(new Error("Erro de rede no upload"));
      xhr.send(fd);
    });

    const data = await promise;
    uploadProgress.hidden = true;
    if(!data.job_id) throw new Error("job_id inválido");

    processing.hidden = false;
    statusText.textContent = "Processando...";

    pollStatus(data.job_id);
  }catch(err){
    uploadProgress.hidden = true;
    feedback.hidden = false;
    feedback.textContent = "Erro: " + err.message;
  }
});

async function pollStatus(jobId){
  const timer = setInterval(async ()=>{
    try{
      const r = await fetch("/status/" + jobId);
      const s = await r.json();
      if(s.error) throw new Error(s.error);
      statusText.textContent = `Status: ${s.status} — ${s.progress || 0}%`;
      if(s.status === "finished"){
        clearInterval(timer);
        processing.hidden = true;
        results.hidden = false;
        zipLink.href = `/download/${jobId}`;
        loadList(jobId);
      }
      if(s.status === "failed"){
        clearInterval(timer);
        processing.hidden = true;
        feedback.hidden = false;
        feedback.textContent = "O processamento falhou.";
      }
    }catch(e){
      clearInterval(timer);
      processing.hidden = true;
      feedback.hidden = false;
      feedback.textContent = "Erro ao consultar status.";
    }
  }, 1200);
}

async function loadList(jobId){
  try{
    const r = await fetch("/list/" + jobId);
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
