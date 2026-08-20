# Psychiatric Hospital Simulator

Simulador de gestión hospitalaria psiquiátrica para Android, hecho en Unity 2D.
El diseño completo (bucle de juego, sistemas clínicos, economía, progresión,
V0.1 → V1.0) está en [`DESIGN.md`](DESIGN.md).

## Estado actual: V0.1

Alcance de esta versión, según la hoja de ruta del diseño:

- **Mapa**: cuadrícula del hospital (40x24 celdas) con piso renderizado.
- **Cámara**: paneo (arrastre táctil / botón central o derecho del mouse) y zoom
  (pellizco táctil / rueda del mouse), acotada a los límites del terreno.
- **Construcción de habitaciones**: paleta de salas cargada desde
  `Assets/StreamingAssets/Data/rooms.json` (nada hardcodeado); modo de
  construcción con validación real de superposición y límites del terreno.
- **Pacientes básicos**: generados proceduralmente (nombre, edad, sexo) desde
  `Assets/StreamingAssets/Data/patient_names.json`, aparecen con el tiempo y
  deambulan por el piso libre.
- **Tiempo**: reloj de día/hora con pausa y velocidades 1x/2x/3x; todo lo demás
  (aparición de pacientes) reacciona a este reloj, no a segundos reales.

Explícitamente fuera de alcance en V0.1 (llegan en versiones posteriores, ver
`DESIGN.md` sección 26): personal, entrevista clínica, síntomas, diagnóstico,
tratamientos, economía, reputación, eventos, guardado.

No hay assets de arte importados todavía: las salas y los pacientes se
representan con sprites generados en tiempo de ejecución (colores planos), a
propósito, para priorizar sistemas funcionales antes que gráficos (regla 27
del diseño).

## Requisitos

- Unity **2022.3 LTS** (o similar 2022.3.x — el patch exacto no es crítico).
- Módulo de build de Android instalado en Unity Hub si se quiere generar APK.

## Cómo abrir el proyecto

1. Abrir esta carpeta como proyecto en Unity Hub / Unity Editor.
2. Unity generará automáticamente los archivos faltantes de `ProjectSettings/`
   y los `.meta` de todos los assets en la primera apertura — es normal.
3. En el menú, ejecutar **`Psychiatric Hospital Simulator > Setup V0.1 Scene`**.
   Esto crea `Assets/Scenes/Main.unity` con un único objeto `GameManager`; todo
   lo demás (cámara, grilla, UI, spawner de pacientes) se construye por código
   al entrar en Play, así que no hay una escena hecha a mano que mantener
   sincronizada.
4. Presionar **Play**.

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
- **Velocidad de tiempo**: botones `||` `1x` `2x` `3x` en la barra superior.

## Arquitectura del código

```
Assets/Scripts/
  Core/       GameManager, TimeManager, CameraController
  Hospital/   HospitalGrid, RoomTypeData/RoomDatabase, RoomInstance,
              HospitalManager, BuildController
  Patients/   PatientData, Patient, PatientManager
  UI/         HudController
  Data/       JsonDataService (carga JSON desde StreamingAssets, funciona
              offline y en Android)
  Utils/      SpriteFactory (sprites generados en runtime)
Assets/Editor/
  SceneSetup.cs   Crea la escena inicial usando la API real del Editor
Assets/StreamingAssets/Data/
  rooms.json, patient_names.json
```

Estos nombres siguen la arquitectura descrita en la sección 24 del diseño
(`GameManager`, `HospitalManager`, `PatientManager`, `TimeManager`, `UIManager`
→ `HudController`). Los managers no incluidos todavía (`StaffManager`,
`DiagnosisSystem`, `TreatmentSystem`, `EconomyManager`, `SaveManager`,
`EventManager`) se agregan en las versiones que los necesitan, para no crear
sistemas a medio terminar.

## Próximos pasos (V0.2)

Personal (psiquiatra, psicólogo, enfermero, etc.), recepción funcional,
consultorio y movimiento real de pacientes hacia destinos asignados — ver
`DESIGN.md` sección 26.
