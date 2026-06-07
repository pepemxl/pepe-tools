let stream = null;
let currentFacingMode = 'environment';
let mediaRecorder = null;
let recordedChunks = [];
let isRecording = false;
let animationFrame = null;
let currentFilter = 'none';

const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const statusEl = document.getElementById('status');

const btnStart = document.getElementById('btnStart');
const btnStop = document.getElementById('btnStop');
const btnSwitch = document.getElementById('btnSwitch');
const btnCapture = document.getElementById('btnCapture');
const btnRecord = document.getElementById('btnRecord');
const filterSelect = document.getElementById('filterSelect');

// Iniciar cámara
async function startCamera() {
    try {
        stopCamera(); // Detener cualquier stream previo

        const constraints = {
            video: {
                facingMode: currentFacingMode,
                width: { ideal: 1280 },
                height: { ideal: 720 }
            }
        };

        stream = await navigator.mediaDevices.getUserMedia(constraints);
        video.srcObject = stream;

        video.onloadedmetadata = () => {
            canvas.width = video.videoWidth || 640;
            canvas.height = video.videoHeight || 480;
            startRendering(); // Iniciar renderizado con filtros
        };

        updateStatus('Cámara iniciada ✓');
    } catch (err) {
        console.error(err);
        alert('Error al acceder a la cámara: ' + err.message);
    }
}

function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        video.srcObject = null;
        stream = null;
    }
    if (animationFrame) cancelAnimationFrame(animationFrame);
    updateStatus('');
}

// Renderizado en tiempo real con filtros
function startRendering() {
    function render() {
        if (!video.srcObject) return;

        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        if (currentFilter !== 'none') {
            applyFilter(currentFilter);
        }

        animationFrame = requestAnimationFrame(render);
    }
    render();
}

// Aplicar filtro en tiempo real (manipulación de píxeles)
function applyFilter(filter) {
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const data = imageData.data;

    for (let i = 0; i < data.length; i += 4) {
        const r = data[i];
        const g = data[i + 1];
        const b = data[i + 2];

        switch (filter) {
            case 'grayscale':
                const gray = 0.34 * r + 0.5 * g + 0.16 * b;
                data[i] = data[i + 1] = data[i + 2] = gray;
                break;
            case 'sepia':
                data[i] = Math.min(255, r * 0.393 + g * 0.769 + b * 0.189);
                data[i + 1] = Math.min(255, r * 0.349 + g * 0.686 + b * 0.168);
                data[i + 2] = Math.min(255, r * 0.272 + g * 0.534 + b * 0.131);
                break;
            case 'invert':
                data[i] = 255 - r;
                data[i + 1] = 255 - g;
                data[i + 2] = 255 - b;
                break;
            case 'brightness':
                data[i] = Math.min(255, r * 1.4);
                data[i + 1] = Math.min(255, g * 1.4);
                data[i + 2] = Math.min(255, b * 1.4);
                break;
            case 'blur':
                // Blur simple (promedio de vecinos) - más lento
                if (i % (canvas.width * 4) !== 0 && i > canvas.width * 4) {
                    data[i] = (r + data[i - 4] + data[i + 4]) / 3;
                    data[i + 1] = (g + data[i - 3] + data[i + 5]) / 3;
                    data[i + 2] = (b + data[i - 2] + data[i + 6]) / 3;
                }
                break;
        }
    }
    ctx.putImageData(imageData, 0, 0);
}

// Capturar y guardar foto automáticamente
function captureAndSave() {
    if (!stream) {
        alert('Inicia la cámara primero');
        return;
    }

    // Asegurar que el canvas tenga el frame actual
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    if (currentFilter !== 'none') applyFilter(currentFilter);

    const link = document.createElement('a');
    link.download = `foto_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();

    updateStatus('¡Foto guardada automáticamente!');
    setTimeout(() => updateStatus(''), 3000);
}

// Grabación de video
function toggleRecording() {
    if (!stream) {
        alert('Inicia la cámara primero');
        return;
    }

    if (!isRecording) {
        // Iniciar grabación
        recordedChunks = [];
        mediaRecorder = new MediaRecorder(stream, { mimeType: 'video/webm;codecs=vp9' });

        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) recordedChunks.push(event.data);
        };

        mediaRecorder.onstop = () => {
            const blob = new Blob(recordedChunks, { type: 'video/webm' });
            const url = URL.createObjectURL(blob);

            const a = document.createElement('a');
            a.href = url;
            a.download = `video_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.webm`;
            a.click();

            URL.revokeObjectURL(url);
            updateStatus('¡Video guardado!');
        };

        mediaRecorder.start();
        isRecording = true;
        btnRecord.textContent = 'Detener Grabación';
        btnRecord.style.background = '#4CAF50';
        updateStatus('Grabando...');
    } else {
        // Detener grabación
        mediaRecorder.stop();
        isRecording = false;
        btnRecord.textContent = 'Grabar Video';
        btnRecord.style.background = '#f44336';
    }
}

function updateStatus(message) {
    statusEl.textContent = message;
}

// Eventos
btnStart.addEventListener('click', startCamera);
btnStop.addEventListener('click', stopCamera);
btnSwitch.addEventListener('click', async () => {
    currentFacingMode = currentFacingMode === 'environment' ? 'user' : 'environment';
    await startCamera();
});
btnCapture.addEventListener('click', captureAndSave);
btnRecord.addEventListener('click', toggleRecording);

filterSelect.addEventListener('change', (e) => {
    currentFilter = e.target.value;
});

// Registro de Service Worker (PWA)
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('service-worker.js')
        .then(() => console.log('Service Worker registrado'))
        .catch(err => console.log('Error SW:', err));
}