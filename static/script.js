function updateProgress() {
    fetch('/progress')
        .then(res => res.json())
        .then(data => {
            document.getElementById('progress-bar').style.width = data.progress + '%';
            if (data.progress < 100) {
                setTimeout(updateProgress, 100);
            }
        });
}