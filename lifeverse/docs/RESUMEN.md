# LIFEVERSE — Resumen en español

_Actualizado: 2026-11-15 (requisitos adicionales incorporados)._ Este documento
resume el estado, las decisiones y el plan. Los documentos técnicos completos
están, por ahora, en inglés.

## Estado actual

**Hito 1 (investigación, arquitectura y herramientas) terminado y pendiente de tu
revisión. Todavía no existe código del juego ni nada jugable.**

Registro de características ([`FEATURE_REGISTRY.md`](FEATURE_REGISTRY.md)): 182 en
total — 170 PLANNED, 3 IMPLEMENTED, 2 TESTED, 6 VERIFIED, 1 BLOCKED. Todo lo que
está VERIFIED son **herramientas**; ninguna característica del juego ha pasado de
PLANNED.

| Elemento | Estado |
|---|---|
| Godot 4.7.2, Blender 5.3.0, plantillas de exportación, SDK de Android | Instalados con un solo comando reproducible |
| Exportación a Linux y Web | VERIFIED: se ejecutan |
| Exportación a Windows | TESTED: `.exe` válido, **nunca ejecutado** (aquí no hay Windows) |
| Exportación a Android | TESTED: APK firmado, **nunca probado en un dispositivo** |
| Exportación a macOS / iOS | BLOCKED: hace falta un Mac |
| Cadena Blender → Godot | VERIFIED |
| Registro de características con estados obligatorios | VERIFIED |

## Tus requisitos adicionales: cómo quedan incorporados

Los dos encargos están guardados tal cual en `docs/requirements/`. Cada
característica del registro indica qué requisito cumple (`B…` = encargo original,
`A…` = requisitos adicionales).

| Requisito | Cómo se resuelve |
|---|---|
| **A1 Vida diaria** | Una sola simulación con tres niveles de zoom: **rutina** (un plan que editas y se ejecuta cada día), **día** (abres un día concreto y lo organizas a mano) y **momento** (una actividad jugada como escena). Higiene, sueño, comida, compras, transporte, hogar, mascotas, aficiones, viajes y fechas señaladas son actividades definidas como datos que afectan a tiempo, dinero, relaciones y atributos. |
| **A2 Interacciones sociales** | Un único motor de conversación: temas que dependen del contexto y de la historia compartida, distintos enfoques, reacciones emocionales, secretos, discusiones y reconciliación, progresión de amistad y romance. Los PNJ inician conversaciones por su cuenta. La entrevista clínica y la entrevista de trabajo usan el mismo motor. |
| **A3 Flujo profesional completo** | Vacantes, solicitudes, entrevistas, contratación o rechazo, contratos, horarios, colegas y supervisores, conflictos, evaluaciones, ascensos, renuncias y despidos, certificaciones, especializaciones, emprendimiento y consulta privada. |
| **A4 Hospital completo** | El hospital es una institución simulada que funciona aunque no estés: departamentos, médicos y enfermeras con turnos, listas de espera, ingresos, altas y traslados, urgencias, documentación, **mecánicas de privacidad y confidencialidad** (cada historia que abres queda registrada y es auditable), presupuestos, equipos y suministros, evaluaciones de calidad y colaboración entre departamentos. |
| **A5 Mundo vivo** | Localidades con barrios, negocios que abren y cierran, ciclo económico, mercado laboral cambiante, calendario social, noticias generadas por lo que ocurre en el mundo, y decisiones que alcanzan a las generaciones siguientes. |
| **A6 Inmersión audiovisual** | Personajes animados en 2D con expresiones faciales según su emoción, animaciones según la actividad, escenas de lugares con día/noche y clima, sonido ambiental y música. La presentación nunca contiene reglas: lo que se ve refleja la simulación. |
| **A7 Contenido y expansión** | Paquetes de contenido: eventos, carreras, especializaciones, instituciones, personalidades, diálogos y actividades se añaden sin tocar el motor. Los paquetes de expansión se cargan como archivos aparte (mecanismo comprobado en el motor). |
| **A8 Accesibilidad e idiomas** | Español e inglés completos en cada hito; texto escalable; opciones de color; intensidad de animación ajustable; controles reasignables; ajustes de audio y subtítulos; dificultad y personalización del juego. |
| **A9 Calidad y producción** | Pruebas de regresión, medición de rendimiento, copias de seguridad y recuperación de partidas, registro de errores, validación de datos, compilación automática, empaquetado, tutoriales, logros y documentación. |
| **A10 Protocolo de verificación** | Registro con los seis estados que pediste. Una herramienta **impide** marcar algo como VERIFIED sin un procedimiento reproducible registrado (comando, fecha, commit, resultado). Antes de empezar un módulo se comprueban sus dependencias. Cada hito produce una versión jugable. |

## Lo que debes saber con franqueza

1. **El alcance se ha duplicado.** La estimación pasó de unas 31.000 a unas 64.000
   líneas de código y unos 3.400 elementos de contenido bilingüe. El conjunto
   equivale a varios juegos comerciales. Este plan entrega un subconjunto
   coherente, en pasos verificados; **no** entrega treinta profesiones terminadas.
2. **El sonido no lo puedo oír.** Puedo generar y cargar audio, pero la calidad de
   música y efectos tendrás que juzgarla tú. Tampoco hay artista ni compositor: los
   gráficos serán vectoriales y procedurales.
3. **La vida diaria no será un minijuego por tarea.** Cepillarse los dientes 30.000
   veces no es jugable. Por defecto es una rutina con consecuencias reales, y
   cualquier día se puede abrir y jugar a mano. Si quieres que alguna actividad
   concreta sea una escena interactiva, dime cuál.
4. **Windows y Android no los puedo ejecutar.** Genero las versiones, pero probarlas
   te toca a ti.

## Hitos

| Hito | Contenido | Estado |
|---|---|---|
| 1 | Investigación, arquitectura, herramientas | ✅ pendiente de revisión |
| 2 | Base jugable y base de producción (guardado, registro de errores, compilación automática, español/inglés) | ⬜ |
| 3a | Personas y conversación: creación de personaje, relaciones, diálogos, familia | ⬜ |
| 3b | Vida diaria: rutinas, compras, hogar, transporte, mascotas, aficiones, viajes | ⬜ |
| 3c | Educación, economía, consecuencias a largo plazo, mundo (primera versión) | ⬜ |
| 4 | Marco de carreras y flujo profesional completo | ⬜ |
| 5a | Psiquiatría clínica | ⬜ |
| 5b | Operación del hospital | ⬜ |
| 6a | Gestión hospitalaria, especialidades, consulta privada | ⬜ |
| 6b | Mundo y PNJ en profundidad | ⬜ |
| 6c | Dos carreras más (propuesta: detective y emprendedor) | ⬜ |
| 7 | Audiovisual, accesibilidad, tutoriales, logros, pulido | ⬜ |
| 8 | Pruebas completas y versión publicable | ⬜ |

Cada paso termina con una versión jugable, pruebas en verde y el registro actualizado.

## Decisiones tuyas pendientes

Si no dices nada, uso el valor por defecto.

| # | Decisión | Por defecto |
|---|---|---|
| 1 | Prototipo de Unity: dejarlo, moverlo a `legacy/` o quitarlo | Dejarlo intacto |
| 2 | ¿En qué vas a jugar las versiones de prueba? (Android, Windows, navegador) | Genero las cuatro |
| 3 | ¿Traduzco también los documentos técnicos al español? | Siguen en inglés, con este resumen |
| 4 | Modelo de tiempo: "Continuar" hasta la siguiente decisión; rutina / día / momento | Sí |
| 5 | Profundidad de la vida diaria: rutinas con consecuencias | Sí; dime si alguna actividad debe ser escena |
| 6 | Nombres clínicos descriptivos, tratamientos abstractos, país ficticio | Sí |
| 7 | Tono: temas adultos tratados con seriedad y sin contenido gráfico | Sí |
| 8 | Carreras del paso 6c | Detective y emprendedor |
| 9 | Carrera sencilla de referencia para el hito 4 | Docente |
| 10 | Origen del audio: generado por script y material CC0, aprobado por ti de oído | Sí; alternativa: lo aportas tú |
| 11 | Instalador de Windows | Solo zip portable |

## Documentos

- [`requirements/`](requirements/) — tus dos encargos, tal cual
- [`FEATURE_REGISTRY.md`](FEATURE_REGISTRY.md) — registro de características y estados
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — arquitectura técnica (inglés); la Parte II cubre los requisitos adicionales
- [`PSYCHIATRY_DESIGN.md`](PSYCHIATRY_DESIGN.md) — psiquiatría y hospital (inglés)
- [`UI_DIRECTION.md`](UI_DIRECTION.md) — dirección de interfaz (inglés)
- [`ROADMAP.md`](ROADMAP.md) — hitos y estimación (inglés)
- [`../PROJECT_STATUS.md`](../PROJECT_STATUS.md), [`DEVLOG.md`](DEVLOG.md),
  [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) — estado, bitácora, problemas conocidos (inglés)
