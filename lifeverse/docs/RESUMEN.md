# LIFEVERSE — Resumen en español

_Actualizado: 2026-11-15._ Este documento resume el estado, las decisiones y el plan.
Los documentos técnicos completos están, por ahora, en inglés.

## Estado actual

**Hito 1 (investigación y arquitectura) terminado y pendiente de tu revisión.
Todavía no existe código del juego ni nada jugable.**

Lo que sí existe y está comprobado:

| Elemento | Estado |
|---|---|
| Godot 4.7.2 (versión estable actual), fijado por checksum | Instalado y probado |
| Blender 5.3.0 | Instalado; cadena Blender → glTF → Godot probada |
| Plantillas de exportación de Godot | Instaladas |
| SDK de Android + clave de depuración | Instalado |
| Exportación a **Linux** | Probada: el binario se ejecuta |
| Exportación a **Web** | Probada: corre en Chromium |
| Exportación a **Windows** | Genera un `.exe` válido; **no ejecutado** (aquí no hay Windows) |
| Exportación a **Android** | Genera un APK firmado y válido; **no probado en un dispositivo** |
| Linter de GDScript (`gdlint`) | Instalado y probado con sintaxis 4.7 |
| Instalación con un solo comando | `tools/setup_dev_env.sh --all` (2 min 47 s desde cero) |

## Hallazgo importante

El repositorio ya contenía un prototipo en **Unity** ("Psychiatric Hospital
Simulator" V0.2). No se ha tocado. LIFEVERSE vive aparte, en `lifeverse/`. Es otro
juego en otro motor, así que se reaprovechan sus ideas de diseño, no su código.

## Decisiones de arquitectura (lo esencial)

- **Un solo mundo.** El jugador, los PNJ y los pacientes son el mismo tipo de
  persona. Un paciente tiene familia, trabajo y memoria, y puede reaparecer en tu vida.
- **Relaciones con memoria.** Lo que alguien siente por ti se calcula a partir de
  recuerdos concretos que se van atenuando; el juego puede explicarte *por qué*.
- **Eventos como datos.** Un único lenguaje de condiciones y otro de efectos sirven
  para eventos, cadenas de historia, acciones de PNJ y resultados profesionales.
  Añadir cientos de eventos no exige tocar el motor.
- **Carreras como módulos.** Cada profesión es un módulo con un contrato fijo,
  construido sobre piezas reutilizables (expediente de caso, entrevista, inferencia,
  reloj de turno). Los turnos que no juegas se resuelven con la misma simulación
  que los que sí juegas: no hay botones que solo den dinero.
- **Psiquiatría.** Cada paciente tiene una verdad oculta que el juego nunca revela.
  Reúnes hallazgos de fuentes que pueden contradecirse, formulas un diagnóstico,
  decides tratamiento y destino, y descubres si acertaste por la evolución del
  paciente. Todo el contenido clínico es ficción, sin fármacos ni dosis reales.
- **Guardado.** Versionado, con escritura atómica y copias de respaldo; se puede
  cerrar el juego en cualquier momento, incluso a mitad de una consulta, y continuar
  exactamente igual.
- **Interfaz.** Vertical primero (como tu referencia), adaptable a escritorio. La
  estructura sigue las capturas que enviaste; la identidad visual será original.
- **Idioma.** Español como idioma principal del juego; inglés como segundo.
- **Sin dependencias externas** en el juego: solo Godot y código propio.

## Alcance realista

La visión completa (unas treinta profesiones, cada una con mecánicas propias) es
trabajo de un estudio durante años y **no** estará terminada al final de este plan.
Este plan entrega:

1. la simulación de vida completa y persistente;
2. el marco de carreras;
3. **psiquiatría con profundidad real**;
4. dos profesiones más (propuesta: detective y emprendedor);
5. una versión probada y exportada.

## Hitos

| Hito | Contenido | Estado |
|---|---|---|
| 1 | Investigación, entorno, arquitectura | ✅ pendiente de revisión |
| 2 | Base jugable: nacer, pasar el tiempo, eventos, guardar/cargar, interfaz básica | ⬜ |
| 3 | Creación de personaje, relaciones, familia, educación, economía, consecuencias | ⬜ |
| 4 | Marco de carreras profesionales | ⬜ |
| 5 | Módulo de psiquiatría (rangos clínicos, especialidad de adultos) | ⬜ |
| 6 | PNJ avanzados, rangos directivos y demás especialidades, más carreras | ⬜ |
| 7 | Pulido, accesibilidad, rendimiento, decisión sobre 3D | ⬜ |
| 8 | Pruebas completas y versión publicable | ⬜ |

## Lo que no puedo comprobar desde aquí

Audio, rendimiento con GPU real, tacto en pantalla, lectores de pantalla, y ejecutar
las versiones de Windows y Android. Eso requiere que pruebes tú las versiones.

## Decisiones tuyas pendientes

Si no dices nada, uso el valor por defecto.

| # | Decisión | Por defecto |
|---|---|---|
| 1 | Prototipo de Unity: dejarlo, moverlo a `legacy/` o quitarlo | Dejarlo intacto |
| 2 | ¿En qué dispositivo vas a jugar las versiones de prueba? (Android, Windows, navegador) | Genero las cuatro; tú eliges |
| 3 | ¿Traduzco también los documentos técnicos al español? | Siguen en inglés, con este resumen |
| 4 | Modelo de tiempo: botón "Continuar" hasta la siguiente decisión; año de 336 días | Sí |
| 5 | Nombres clínicos descriptivos, tratamientos abstractos, país ficticio | Sí |
| 6 | Tono: temas adultos tratados con seriedad y sin contenido gráfico | Sí |
| 7 | Carreras adicionales del hito 6 | Detective y emprendedor |
| 8 | Carrera sencilla de referencia para el hito 4 | Docente |

## Documentos

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — arquitectura técnica completa (inglés)
- [`PSYCHIATRY_DESIGN.md`](PSYCHIATRY_DESIGN.md) — diseño del módulo de psiquiatría (inglés)
- [`UI_DIRECTION.md`](UI_DIRECTION.md) — dirección de interfaz (inglés)
- [`ROADMAP.md`](ROADMAP.md) — hitos y estimación de trabajo (inglés)
- [`../PROJECT_STATUS.md`](../PROJECT_STATUS.md), [`DEVLOG.md`](DEVLOG.md),
  [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) — estado, bitácora, problemas conocidos (inglés)
