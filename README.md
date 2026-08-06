# Tabla de posiciones Liga de Primera — actualización automática

Esta carpeta contiene todo lo necesario para que la tabla de posiciones se actualice
sola, sin depender de que nadie la abra ni de que Claude corra nada. El mecanismo:

1. **`scrape.py`**: lee `campeonatochileno.cl` con código (no con un modelo de IA) y
   guarda los datos en `data.json`. Si no logra encontrar la tabla o extrae menos de
   10 clubes, termina con error y NO sobreescribe `data.json` — así nunca se publican
   datos incompletos.
2. **`.github/workflows/update.yml`**: hace que GitHub corra `scrape.py` solo, cada
   20 minutos, para siempre, gratis (repos públicos tienen minutos de Actions
   ilimitados). Si el scraper falla, GitHub te manda un correo automático.
3. **`index.html`**: la página que ve el lector. Lee `data.json` y se refresca sola
   cada 5 minutos mientras esté abierta. Esta es la URL que va en el iframe de Composer.

## Pasos para dejarlo funcionando (una sola vez, ~10 minutos)

1. **Crear el repositorio en GitHub**
   - Ve a github.com → botón verde "New" → nombre sugerido: `liga-primera-tabla`
   - Marca **Public** (Pages gratis solo funciona con repos públicos; los datos que
     se publican son de todos modos públicos, la tabla de la ANFP).
   - Crea el repo vacío (sin README, sin .gitignore).

2. **Subir estos archivos**
   - Opción simple sin git: en la página del repo, botón "Add file" → "Upload files",
     y arrastra `scrape.py`, `requirements.txt`, `index.html`, `data.json`.
   - Para el workflow, como GitHub no deja arrastrar carpetas fácil desde el navegador:
     "Add file" → "Create new file" → en el nombre escribe
     `.github/workflows/update.yml` (con las barras, así se crean las carpetas solas)
     → pega el contenido de ese archivo → "Commit changes".

3. **Dar permiso de escritura al workflow**
   - Settings del repo → Actions → General → baja hasta "Workflow permissions"
   - Marca **"Read and write permissions"** → Save.
   - (Sin esto, el scraper corre pero no puede guardar los cambios.)

4. **Activar GitHub Pages**
   - Settings del repo → Pages
   - En "Build and deployment" → Source: **Deploy from a branch**
   - Branch: **main**, carpeta: **/ (root)** → Save.
   - GitHub te va a dar una URL tipo `https://TU-USUARIO.github.io/liga-primera-tabla/`
     (tarda 1-2 minutos en quedar activa la primera vez).

5. **Probar el scraper manualmente antes de esperar los 20 minutos**
   - Pestaña "Actions" del repo → clic en "Actualizar tabla Liga de Primera"
     → botón "Run workflow" → "Run workflow" de nuevo para confirmar.
   - Espera ~30 segundos y revisa si el paso quedó verde (✅) o rojo (❌).
   - Si queda rojo, entra al log y me pasas el error tal cual — probablemente el
     sitio cambió algo en su estructura HTML y hay que ajustar `scrape.py`.

6. **Embeber en Composer**
   - Usa como `src` del iframe: `https://TU-USUARIO.github.io/liga-primera-tabla/`
   - Esa URL no cambia nunca, aunque los datos se actualicen cada 20 minutos.

## Ajustar la frecuencia

En `.github/workflows/update.yml`, la línea `cron: "*/20 * * * *"` corre cada 20
minutos. Para cambiarla a cada 10 minutos: `*/10 * * * *`. GitHub corre estos cron en
UTC, pero como es un intervalo relativo (cada N minutos) no importa la zona horaria.

## Ajustar las franjas de zona (Libertadores / Sudamericana / descenso)

En `index.html`, al inicio del `<script>`, están estas constantes:

```js
const ZONE_LIBERTADORES_DIRECTO_HASTA = 2;
const ZONE_PREVIA_HASTA = 4;
const ZONE_SUDAMERICANA_HASTA = 7;
const ZONE_DESCENSO_DESDE = 16;
```

Las dejé según el orden estándar del torneo, pero no las pude confirmar 1 a 1 contra
el sitio fuente (esa info viene por color, se pierde al extraer el HTML). Revísalas
tú una vez contra campeonatochileno.cl y ajusta los números si hace falta.
