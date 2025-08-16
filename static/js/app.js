
document.addEventListener('DOMContentLoaded', () => {
  const fileInput = document.getElementById('file');
  const preview = document.getElementById('pdfPreview');
  const form = document.getElementById('split-form');
  const rangesWrap = document.getElementById('ranges-wrap');
  const progress = document.getElementById('progress');
  const bar = document.getElementById('bar');
  const pct = document.getElementById('pct');
  const cut = document.getElementById('cutEffect');

  // Toggle ranges input
  form.addEventListener('change', (e) => {
    if (e.target.name === 'mode') {
      const useRanges = e.target.value === 'ranges';
      rangesWrap.style.display = useRanges ? '' : 'none';
    }
  });

  // Show preview using a blob URL (no heavy libs)
  fileInput.addEventListener('change', () => {
    const file = fileInput.files && fileInput.files[0];
    if (file) {
      const url = URL.createObjectURL(file);
      preview.src = url;
      preview.style.display = 'block';
    } else {
      preview.removeAttribute('src');
      preview.style.display = 'none';
    }
  });

  // AJAX submit to track upload progress & download result
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData(form);
    const file = fileInput.files && fileInput.files[0];
    if (!file) return;

    progress.hidden = false;
    bar.style.width = '0%';
    pct.textContent = '0%';
    cut.hidden = true;

    const xhr = new XMLHttpRequest();
    xhr.open('POST', form.action);

    xhr.responseType = 'blob';

    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable) {
        const per = Math.round((event.loaded / event.total) * 100);
        bar.style.width = per + '%';
        pct.textContent = per + '%';
      }
    });

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        // Animate "cut" effect
        cut.hidden = false;
        // Try to get filename from headers
        const disp = xhr.getResponseHeader('Content-Disposition') || '';
        let filename = 'resultado.pdf';
        const match = /filename="([^"]+)"/.exec(disp);
        if (match) filename = match[1];

        const blob = xhr.response;
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        setTimeout(() => { window.URL.revokeObjectURL(url); }, 1000);
      } else {
        alert('Erro: ' + xhr.status + ' ' + xhr.statusText);
      }
    };

    xhr.onerror = () => alert('Falha na rede. Tente novamente.');
    xhr.send(fd);
  });
});
