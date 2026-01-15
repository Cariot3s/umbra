document.addEventListener("DOMContentLoaded", () => {

    const playBtn = document.getElementById("play-btn");
    const downloadBtn = document.getElementById("download-btn");
    const audio = document.getElementById("audio");

    // Reproducir audio desde el principio
    playBtn.addEventListener("click", () => {
        audio.currentTime = 0;
        audio.play();
        playBtn.disabled = true;
    });

    // Cuando termina el audio, mostrar botón de descarga
    audio.addEventListener("ended", () => {
        downloadBtn.classList.remove("hidden");
        playBtn.disabled = false;
    });

    // Descargar el audio
    downloadBtn.addEventListener("click", () => {
        const link = document.createElement("a");
        link.href = "/core/audio/origen.mp3";
        link.download = "origen.mp3";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });

});
