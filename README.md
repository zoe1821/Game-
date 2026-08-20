# Psychiatric Hospital Simulator

Simulador de gestión hospitalaria psiquiátrica para Android, hecho en Unity 2D.
El diseño completo (bucle de juego, sistemas clínicos, economía, progresión,
V0.1 → V1.0) está en [`DESIGN.md`](DESIGN.md).

## Estado actual: V0.2

Alcance acumulado hasta esta versión, según la hoja de ruta del diseño:

**V0.1**

- **Mapa**: cuadrícula del hospital (40x24 celdas) con piso renderizado.
- **Cámara**: paneo (arrastre táctil / botón central o derecho del mouse) y zoom
  (pellizco táctil / rueda del mouse), acotada a los límites del terreno.
- **Construcción de habitaciones**: paleta de salas cargada desde
  `Assets/StreamingAssets/Data/rooms.json` (nada hardcodeado); modo de
  construcción con validación real de superposición y límites del terreno.
- **Tiempo**: reloj de día/hora con pausa y velocidades 1x/2x/3x; todo lo demás
  reacciona a este reloj, no a segundos reales.

**V0.2**

- **Personal**: panel lateral para contratar Recepcionista, Psiquiatra y
  Psicólogo (roles y datos en `Assets/StreamingAssets/Data/staff.json`). Al
  contratar, el empleado camina hasta la primera sala construida que le
  corresponda y se queda trabajando ahí; si aún no existe esa sala, espera y
  se asigna automáticamente en cuanto se construye una.
- **Recepción**: la recepcionista registra a cada paciente que llega antes de
  derivarlo a consulta.
- **Consultorio**: los consultorios de psiquiatría/psicología atienden un
  paciente a la vez; si el profesional está ocupado, el paciente espera en la
  puerta (si hay más de un profesional del mismo rol, el paciente va al que
  esté libre en vez de amontonarse siempre en el primero).
- **Movimiento de pacientes**: reemplaza el deambular aleatorio de V0.1 por
  navegación real sobre la grilla (BFS que esquiva salas construidas) hacia
  recepción, consultorio y salida. Si el hospital todavía no tiene recepción
  contratada, el paciente deambula cerca de la entrada (comportamiento
  honesto de "hospital no operativo todavía", no un estado roto) y retoma el
  flujo apenas se contrata personal.

Explícitamente fuera de alcance todavía (llegan en versiones posteriores, ver
`DESIGN.md` sección 26): entrevista clínica, síntomas, historia clínica,
diagnóstico diferencial, tratamientos, hospitalización, emergencias,
economía, reputación, eventos, IA de pacientes, guardado.

No hay assets de arte importados todavía: las salas, pacientes y personal se
representan con sprites generados en tiempo de ejecución (colores planos), a
propósito, para priorizar sistemas funcionales antes que gráficos (regla 27
del diseño). Contratar personal es gratis en esta versión porque el sistema
de economía (V0.7) todavía no existe — no se simula un costo falso.

## Requisitos

- Unity **2022.3 LTS** (o similar 2022.3.x — el patch exacto no es crítico).
- Módulo de build de Android instalado en Unity Hub si se quiere generar APK.

## Cómo abrir el proyecto

1. Abrir esta carpeta como proyecto en Unity Hub / Unity Editor.
2. Unity generará automáticamente los archivos faltantes de `ProjectSettings/`
   y los `.meta` de todos los assets en la primera apertura — es normal.
3. En el menú, ejecutar **`Psychiatric Hospital Simulator > Setup V0.1 Scene`**.
   Esto crea `Assets/Scenes/Main.unity` con un único objeto `GameManager`; todo
   lo demás (cámara, grilla, UI, personal, pacientes) se construye por código
   al entrar en Play, así que no hay una escena hecha a mano que mantener
   sincronizada. (El nombre del menú quedó de V0.1; sigue siendo el único
   paso de configuración necesario.)
4. Presionar **Play**.
5. Construir una **Recepción**, un **Consultorio Psiquiátrico** y/o un
   **Consultorio de Psicología** desde la barra inferior, y contratar el
   personal correspondiente desde el panel izquierdo, para ver el flujo
   completo de un paciente.

(Opcional) En *Project Settings > Player > Resolution and Presentation*,
fijar la orientación por defecto en *Landscape Left* — el juego ya la fuerza
por código al iniciar, pero configurarla también en Player Settings evita el
parpadeo inicial en algunos dispositivos Android.

## Controles (Editor / mouse, equivalen a los gestos táctiles)

- **Paneo**: arrastrar con el botón derecho o central del mouse (1 dedo en
  táctil).
- **Zoom**: rueda del mouse (pellizco con 2 dedos en táctil).
- **Construir**: tocar un botón de sala en la barra inferior, luego tocar una
  celda libre del mapa para colocarla. El botón `X` cancela el modo
  construcción.
- **Contratar personal**: tocar un botón del panel izquierdo.
- **Velocidad de tiempo**: botones `||` `1x` `2x` `3x` en la barra superior.

## Arquitectura del código

```
Assets/Scripts/
  Core/       GameManager, TimeManager, CameraController
  Hospital/   HospitalGrid, GridPathfinder, GridMover, RoomTypeData/
              RoomDatabase, RoomInstance, HospitalManager, BuildController
  Staffing/   StaffData/StaffRoleData/StaffRoleDatabase, Staff, StaffManager
  Patients/   PatientData, Patient, PatientManager
  UI/         HudController
  Data/       JsonDataService (carga JSON desde StreamingAssets, funciona
              offline y en Android)
  Utils/      SpriteFactory (sprites generados en runtime)
Assets/Editor/
  SceneSetup.cs   Crea la escena inicial usando la API real del Editor
Assets/StreamingAssets/Data/
  rooms.json, staff.json, patient_names.json
```

Estos nombres siguen la arquitectura descrita en la sección 24 del diseño
(`GameManager`, `HospitalManager`, `StaffManager`, `PatientManager`,
`TimeManager`, `UIManager` → `HudController`). Los managers no incluidos
todavía (`DiagnosisSystem`, `TreatmentSystem`, `EconomyManager`,
`SaveManager`, `EventManager`) se agregan en las versiones que los necesitan,
para no crear sistemas a medio terminar.

`GridMover` (movimiento por celdas con pathfinding BFS) es compartido por
`Patient` y `Staff` para no duplicar la lógica de navegación.

## Próximos pasos (V0.3)

Entrevista clínica (preguntas por categoría), síntomas y historia clínica —
ver `DESIGN.md` sección 26.
