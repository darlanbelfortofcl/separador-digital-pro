const form=document.getElementById("uploadForm");
const fileInput=document.getElementById("pdf");
const fileName=document.getElementById("fileName");
const progressBox=document.getElementById("progressBox");
const progressBar=document.getElementById("progressBar");
const progressPercent=document.getElementById("progressPercent");
const progressStatus=document.getElementById("progressStatus");
const resultBox=document.getElementById("resultBox");
const downloadLink=document.getElementById("downloadLink");

if(fileInput){ fileInput.addEventListener("change", ()=>{ fileName.textContent=fileInput.files?.[0]?.name||"Nenhum arquivo selecionado"; }); }

if(form){
  form.addEventListener("submit", async (e)=>{
    e.preventDefault();
    resultBox.classList.add("hidden");
    progressBox.classList.remove("hidden");
    progressBar.style.width="0%"; progressPercent.textContent="0%"; progressStatus.textContent="Iniciando...";

    const fd=new FormData(form);
    const resp=await fetch("/processar",{method:"POST",body:fd});
    const data=await resp.json();
    if(!data.ok){ progressStatus.textContent=data.msg||"Falha ao iniciar."; return; }

    const jobId=data.job_id;
    const es=new EventSource(`/eventos/${jobId}`);
    es.onmessage=(ev)=>{
      try{
        const payload=JSON.parse(ev.data.replace(/'/g,'"'));
        const p=Math.max(0,Math.min(100,payload.percent??0));
        progressBar.style.width=p+"%"; progressPercent.textContent=p+"%"; progressStatus.textContent=payload.status||"";
        if(p>=100 && payload.download){ downloadLink.href=payload.download; resultBox.classList.remove("hidden"); es.close(); }
      }catch(_){}
    };
  });
}
