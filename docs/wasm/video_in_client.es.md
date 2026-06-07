# Guía Técnica: Desarrollo de Procesamiento de Video en el Cliente con WebAssembly (Wasm) y PWA

El procesamiento de video directamente en el navegador ha experimentado una revolución gracias a la madurez de **WebAssembly (Wasm)** y la evolución de las **Progressive Web Apps (PWA)**. Anteriormente, las tareas intensivas como la transcodificación, edición o aplicación de filtros requerían enviar archivos pesados a un servidor. Hoy en día, es posible realizar estas operaciones de forma local, segura y con rendimiento casi nativo.

Esta guía detalla la arquitectura, herramientas, desafíos y mejores prácticas para desarrollar aplicaciones web progresivas capaces de manipular video en el lado del cliente utilizando WebAssembly y tecnologías complementarias.


## 1. El Ecosistema de Procesamiento de Video en el Navegador

Para trabajar con video en el cliente, existen múltiples enfoques, pero WebAssembly destaca por su capacidad para ejecutar código C/C++ y Rust en el navegador a velocidades cercanas a las nativas [1]. 

A la hora de diseñar la arquitectura, es crucial entender las herramientas disponibles:

| Tecnología | Descripción | Casos de Uso Ideales |
| : | : | : |
| **WebAssembly (Wasm)** | Permite ejecutar bibliotecas maduras (como FFmpeg) en el navegador compiladas a bytecode. | Transcodificación compleja, muxing/demuxing, soporte de formatos heredados. |
| **WebCodecs API** | API nativa del navegador que proporciona acceso de bajo nivel a los codificadores y decodificadores de hardware. | Procesamiento en tiempo real, decodificación de alta velocidad acelerada por hardware. |
| **WebGPU / WebGL** | APIs para aprovechar la tarjeta gráfica del dispositivo. | Renderizado, aplicación de filtros visuales y efectos en tiempo real. |

En arquitecturas modernas, es común **combinar estas tecnologías**. Por ejemplo, usar WebAssembly (FFmpeg) para extraer el audio y manejar contenedores (muxing), mientras se utiliza WebCodecs para la decodificación y codificación acelerada por hardware [2].



## 2. Herramientas Clave: FFmpeg.wasm

**FFmpeg.wasm** es la biblioteca estándar de facto para el procesamiento de video basado en WebAssembly. Es un port puro de FFmpeg a WebAssembly/JavaScript, lo que permite grabar, convertir y transmitir video y audio directamente dentro del navegador [3].

### Conceptos Centrales de FFmpeg.wasm

1. **Web Workers:** La transcodificación multimedia es intensiva. FFmpeg.wasm delega automáticamente estas tareas a un Web Worker (`ffmpeg.worker`) para no bloquear el hilo principal de la interfaz de usuario (UI).
2. **Sistema de Archivos Virtual (MEMFS):** WebAssembly no tiene acceso directo al disco duro del usuario por razones de seguridad. FFmpeg.wasm crea un sistema de archivos virtual en memoria. Los archivos deben cargarse en este sistema antes de procesarse y los resultados deben leerse desde él.
3. **Núcleos (Cores):** El motor de FFmpeg.wasm es intercambiable. Existen versiones de un solo hilo (`@ffmpeg/core`) y versiones multihilo (`@ffmpeg/core-mt`) que ofrecen mayor rendimiento aprovechando múltiples Web Workers [3].

### Ejemplo Básico de Transcodificación

```javascript
import { FFmpeg } from '@ffmpeg/ffmpeg';
import { fetchFile } from '@ffmpeg/util';

const ffmpeg = new FFmpeg();

async function transcodeVideo(inputFile) {
  // 1. Cargar el núcleo de FFmpeg
  await ffmpeg.load({
    coreURL: '/assets/ffmpeg-core.js',
    wasmURL: '/assets/ffmpeg-core.wasm',
  });

  // 2. Escribir el archivo en el sistema de archivos virtual de Wasm
  await ffmpeg.writeFile('input.webm', await fetchFile(inputFile));

  // 3. Ejecutar el comando FFmpeg
  await ffmpeg.exec(['-i', 'input.webm', 'output.mp4']);

  // 4. Leer el resultado
  const data = await ffmpeg.readFile('output.mp4');
  
  // 5. Crear una URL para el reproductor de video
  const videoUrl = URL.createObjectURL(new Blob([data.buffer], { type: 'video/mp4' }));
  return videoUrl;
}
```


## 3. Integración en una PWA (Progressive Web App)

El uso de WebAssembly dentro de una PWA permite crear aplicaciones de edición de video que funcionan **completamente offline**. Una vez que los archivos Wasm y el código JavaScript se almacenan en caché, la aplicación no requiere conexión a internet para procesar videos.

### Estrategia de Service Worker

Para que la PWA funcione offline y cargue rápidamente, el Service Worker debe almacenar en caché los binarios de WebAssembly (`.wasm`) y los scripts de los Web Workers.

```javascript
// sw.js (Ejemplo simplificado)
const CACHE_NAME = 'video-editor-v1';
const ASSETS_TO_CACHE = [
  '/',
  '/index.html',
  '/app.js',
  '/assets/ffmpeg-core.js',
  '/assets/ffmpeg-core.wasm', // Binario Wasm
  '/assets/ffmpeg-core.worker.js' // Worker para multihilo
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS_TO_CACHE))
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => response || fetch(event.request))
  );
});
```


## 4. El Desafío del Multihilo y SharedArrayBuffer

Para lograr un rendimiento aceptable en el procesamiento de video (especialmente en resoluciones HD o 4K), es imperativo utilizar la versión multihilo de FFmpeg.wasm. Sin embargo, el multihilo en WebAssembly depende de la API `SharedArrayBuffer` [4].

Debido a vulnerabilidades de seguridad históricas (como Spectre), los navegadores modernos restringen el uso de `SharedArrayBuffer` a contextos de **Aislamiento de Origen Cruzado (Cross-Origin Isolation)**.

### Configuración de Cabeceras COOP y COEP

Para habilitar `SharedArrayBuffer`, tu servidor debe enviar obligatoriamente las siguientes cabeceras HTTP [5]:

```http
Cross-Origin-Embedder-Policy: require-corp
Cross-Origin-Opener-Policy: same-origin
```

**Problema común en PWAs estáticas (ej. GitHub Pages):**
Si alojas tu PWA en un servicio estático donde no puedes modificar las cabeceras HTTP del servidor, puedes utilizar un "Service Worker mágico" (como la biblioteca `coi-serviceworker`) que intercepta las peticiones y añade estas cabeceras en el lado del cliente [5].



## 5. Limitaciones de WebAssembly y Alternativas Modernas

Aunque FFmpeg.wasm es poderoso, presenta limitaciones significativas en un entorno de producción:

1. **Límite de Memoria:** WebAssembly (en su versión actual de 32 bits) tiene un límite estricto de memoria de 4 GB. Dado que FFmpeg.wasm carga el archivo completo en la memoria virtual antes de procesarlo, intentar editar un video de 2 GB puede hacer que la pestaña del navegador colapse por falta de memoria [6].
2. **Falta de Aceleración por Hardware:** FFmpeg.wasm realiza la codificación y decodificación por software utilizando la CPU. No puede aprovechar el hardware dedicado (GPU) del dispositivo, lo que resulta en tiempos de exportación lentos y alto consumo de batería en móviles [6].
3. **Tamaño del Bundle:** Los binarios de FFmpeg.wasm pueden pesar más de 30 MB, lo que penaliza el tiempo de carga inicial de la PWA.

### La Evolución: WebCodecs + WebAssembly

Para superar estas limitaciones, la arquitectura moderna de edición de video web (utilizada por herramientas avanzadas) combina WebCodecs y WebAssembly:

* **WebCodecs:** Se encarga de la decodificación y codificación del video, delegando el trabajo a la GPU del dispositivo (aceleración por hardware). Esto es drásticamente más rápido y consume menos memoria [2].
* **WebAssembly:** Se utiliza exclusivamente para el "Muxing/Demuxing" (empaquetar y desempaquetar el flujo de video y audio en contenedores como MP4 o WebM) utilizando bibliotecas ligeras (ej. `mp4box.js` o versiones reducidas de FFmpeg) [2].
* **Canvas / WebGL / WebGPU:** Se utilizan para renderizar los fotogramas decodificados, aplicar filtros, superponer texto o realizar recortes, antes de enviar los fotogramas modificados de vuelta a WebCodecs para su codificación [1].

Esta arquitectura en "streaming" procesa el video fotograma a fotograma, evitando cargar todo el archivo en la RAM, lo que soluciona el límite de memoria de Wasm y mejora exponencialmente la velocidad [6].



## 6. Mejores Prácticas para el Desarrollo

1. **Gestión de Memoria:** Si usas FFmpeg.wasm puro, asegúrate de eliminar los archivos del sistema de archivos virtual (`ffmpeg.deleteFile('archivo.mp4')`) inmediatamente después de usarlos para liberar memoria.
2. **Aislamiento del Hilo Principal:** Nunca ejecutes lógica intensiva de Wasm en el hilo principal. Asegúrate de que tu instancia de FFmpeg o tu código Wasm personalizado se ejecute en Web Workers.
3. **Manejo de Errores y Caídas:** El procesamiento de video puede hacer que el navegador elimine la pestaña si consume demasiados recursos. Implementa guardados automáticos del estado del proyecto en IndexedDB.
4. **Optimización de la PWA:** Utiliza estrategias de carga diferida (Lazy Loading) para los binarios `.wasm`. No los descargues hasta que el usuario realmente inicie una acción de edición de video.



## Referencias

[1] [WebrtcHacks](https://webrtchacks.com/video-frame-processing-on-the-web-webassembly-webgpu-webgl-webcodecs-webnn-and-webtransport/). "Video Frame Processing on the Web – WebAssembly, WebGPU, WebGL, WebCodecs, WebNN, and WebTransport".
[2] [Dev.to](https://dev.to/danielfulop/building-a-video-editor-completely-on-the-frontend-ffmpeg-webcodecs-webassembly-and-react-1cfb) "Building a video editor completely on the frontend: FFMpeg, WebCodecs, WebAssembly and React".
[3] [FFmpeg.wasm](https://ffmpegwasm.netlify.app/docs/overview/) Official Documentation. "Overview".
[4] [MDN Web Docs](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cross-Origin-Embedder-Policy) "Cross-Origin-Embedder-Policy".
[5] [Thomas Steiner's Blog](https://blog.tomayac.com/2025/03/08/setting-coop-coep-headers-on-static-hosting-like-github-pages/) "Setting the COOP and COEP headers on static hosting like GitHub Pages".
[6] [Dayverse.id](https://dayverse.id/en/articles/best-ffmpeg-wasm-alternatives-client-side/) "The Best ffmpeg.wasm Alternatives for Client-Side Video Processing".
