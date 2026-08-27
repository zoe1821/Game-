# Cómo ver la app funcionando

Tres formas, de la más fácil a la que da más control.

---

## 1. Desde el celular, sin computadora (Android)

**Lo que necesitas:** un teléfono Android. Nada más.

1. Entra desde el celular a
   **https://github.com/zoe1821/Game-/releases/tag/apk-latest**
2. Baja hasta el final y descarga el archivo que termina en `.apk`.
3. Ábrelo. Android va a decir algo como *"por seguridad, tu teléfono no puede
   instalar apps de esta fuente"*. Es normal: das a **Configuración**, activas
   el permiso para el navegador, y vuelves atrás.
4. Instalar. Ya está.

La app arranca en **modo demostración**: trae un perfil de ejemplo y funciona
sin ningún servidor. Sale un aviso arriba que lo dice, y no se puede quitar a
propósito: la app no debe aparentar que guarda algo que no guarda.

Cada vez que cambia el código, GitHub compila una versión nueva sola y la deja
en ese mismo enlace.

> **Si no aparece el archivo:** significa que la compilación aún no ha
> terminado o falló. Se ve en la pestaña **Actions** del repositorio.

---

## 2. Desde el celular, con la computadora encendida (Android y iPhone)

Sirve para iPhone, y para ver los cambios al instante mientras se programa.

1. En el teléfono, instala **Expo Go** (gratis, está en las dos tiendas).
2. En la computadora:

```bash
git clone https://github.com/zoe1821/Game-.git
cd Game-/hairapp/mobile
npm install
npx expo start
```

3. Escanea el código QR que sale. Con la cámara si es iPhone, desde dentro de
   Expo Go si es Android.

Las dos cosas tienen que estar en la **misma red WiFi**.

---

## 3. Con el backend de verdad

Solo hace falta para probar el guardado real, el escaneo de fotos y las
suscripciones.

```bash
cd Game-/hairapp/backend
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"

# Crear la base de datos
TRICHON_DATABASE_URL="sqlite:///./dev.db" .venv/bin/python -m alembic upgrade head

# Arrancar. El 0.0.0.0 es importante: sin eso el teléfono no lo alcanza.
TRICHON_DATABASE_URL="sqlite:///./dev.db" \
  .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Y en `hairapp/mobile/app.json`, cambia estas dos líneas:

```json
"apiBaseUrl": "http://192.168.1.40:8000",
"demoMode": false
```

Poniendo **la IP de tu computadora**, no `localhost`: desde el teléfono,
`localhost` es el propio teléfono. Para saberla:

- **Windows:** `ipconfig` → *Dirección IPv4*
- **Mac o Linux:** `ipconfig getifaddr en0` o `hostname -I`

---

## Preguntas que salen siempre

**¿Cuánto cuesta esto?**
Nada. Ni la compilación, ni Expo Go, ni instalar el APK. Solo cuesta dinero
**publicar en las tiendas**: Google Play son 25 USD una vez, Apple 99 USD al
año.

**¿Puedo pasarle el APK a alguien para que lo pruebe?**
Sí, el enlace de la release es público. Es la forma más barata de enseñárselo
a alguien antes de pagar nada.

**¿Por qué en iPhone no se puede igual?**
Apple no permite instalar apps fuera de la App Store. No hay forma gratuita
de saltárselo, y no conviene intentarlo.

**Los datos de la demostración, ¿son inventados?**
No. Se generan ejecutando el motor real del proyecto
(`backend/scripts/generate_demo_fixtures.py`) y congelando el resultado. Las
rutinas, las explicaciones y los niveles de confianza que ves son los que
produce el sistema de verdad.
