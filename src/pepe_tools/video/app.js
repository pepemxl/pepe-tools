let stream = null;
let currentFacingMode = 'environment'; // 'environment' = trasera, 'user' = frontal

const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const photo = document.getElementById('photo');

const btnStart = document.getElementById('btnStart');
const btnStop = document.getElementById('btnStop');
const btnCapture = document.getElementById('btnCapture');
const btnSwitch = document.getElementById('btnSwitch');

// Iniciar cámara
async function startCamera() {
    try {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }

        const constraints = {
            video: {
                facingMode: currentFacingMode,
                width: { ideal: 1280 },
                height: { ideal: 720 }
            }
        };

        stream = await navigator.mediaDevices.getUserMedia(constraints);
        video.srcObject = stream;

        // Esperar a que el video esté listo
        video.onloadedmetadata = () => {
            canvas.width = video.videoWidth || 640;
            canvas.height = video.videoHeight || 480;
        };

        console.log('Cámara iniciada');
    } catch (error) {
        console.error('Error al acceder a la cámara:', error);
        alert('No se pudo acceder a la cámara. Asegúrate de dar permiso.');
    }
}

// Detener cámara
function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        video.srcObject = null;
        stream = null;
    }
}

// Capturar imagen del video y dibujarla en el canvas
function captureToCanvas() {
    if (!stream) {
        alert('Primero inicia la cámara');
        return;
    }

    // Dibujar el frame actual del video en el canvas
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Opcional: convertir canvas a imagen y mostrarla abajo
    const dataUrl = canvas.toDataURL('image/png');
    photo.src = dataUrl;
}

// Cambiar entre cámara frontal y trasera
async function switchCamera() {
    currentFacingMode = currentFacingMode === 'environment' ? 'user' : 'environment';
    await startCamera();
}

// Event listeners
btnStart.addEventListener('click', startCamera);
btnStop.addEventListener('click', stopCamera);
btnCapture.addEventListener('click', captureToCanvas);
btnSwitch.addEventListener('click', switchCamera);

// Iniciar automáticamente al cargar (opcional)
window.addEventListener('load', () => {
    // Puedes llamar a startCamera() aquí si quieres que inicie solo
});

if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('service-worker.js')
        .then(reg => console.log('Service Worker registrado'))
        .catch(err => console.log('Error SW:', err));
}