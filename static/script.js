document.getElementById("uploadForm").addEventListener("submit", async function(e) {
    e.preventDefault();
    const files = document.getElementById("fileInput").files;
    if (!files.length) return alert("Selecione ao menos um PDF");

    const formData = new FormData();
    for (let file of files) {
        formData.append("files", file);
    }

    const res = await fetch("/upload", { method: "POST", body: formData });
    const data = await res.json();
    if (!data.job_id) return alert("Erro no upload");

    const jobId = data.job_id;
    const statusDiv = document.getElementById("status");
    const downloadLink = document.getElementById("downloadLink");

    const interval = setInterval(async () => {
        const statusRes = await fetch(`/status/${jobId}`);
        const statusData = await statusRes.json();
        statusDiv.textContent = `Status: ${statusData.status}`;
        if (statusData.status === "concluído") {
            clearInterval(interval);
            downloadLink.href = `/download/${jobId}`;
            downloadLink.style.display = "block";
            downloadLink.textContent = "Baixar Arquivo ZIP";
        }
    }, 2000);
});
