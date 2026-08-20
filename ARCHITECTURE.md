# Arquitectura

## Principio central: "la IA interpreta, el motor ejecuta"

Todo el diseño gira alrededor de una separación estricta:

- **`RPG.AI`** (`IIntentInterpreter`, `RuleBasedIntentInterpreter`) convierte el texto libre
  del jugador en una `ActionIntent` (qué quiere hacer, sobre qué/quién). **Nunca** toca vida,
  dinero, inventario, posiciones ni memoria directamente.
- **`ActionExecutor`** recibe esa intención ya interpretada y decide si es físicamente/
  narrativamente posible. Si lo es, es el **único** responsable de modificar el estado real del
  juego (llamando a `PlayerStats`, `InventorySystem`, `WorldObject`, `PowerController`,
  `NPCController`, etc.).
- **`INPCResponder`** (`RuleBasedNPCResponder`) genera la línea de diálogo/reacción de un NPC
  a partir de su personalidad, relación y emoción — tampoco modifica estado, solo narra.

Esto significa que **sustituir el intérprete por uno basado en un modelo de lenguaje real**
(por ejemplo la API de Claude) en el futuro es un cambio aislado: solo hay que implementar
`IIntentInterpreter` (y opcionalmente `INPCResponder`) de nuevo; `ActionExecutor` y el resto
del motor no cambian una línea.

## Estructura de carpetas

```
Assets/_Project/Scripts/
  Core/        GameManager (orquestador), EventBus (eventos desacoplados), CameraFollow
  Time/        GameDateTime, TimeManager (minuto -> hora -> dia -> semana -> mes -> anio)
  Player/      PlayerController (movimiento), PlayerStats (vida/energia/dinero), PlayerInteractor
  NPC/         NPCData (plantilla, ScriptableObject), NPCState (estado en vivo), NPCController,
               NPCRoutine (rutina diaria basica)
  Memory/      MemoryEntry, MemoryStore (memoria persistente reutilizable por cualquier NPC)
  World/       Interactable (contrato comun), WorldObjectData (plantilla), WorldObject
               (instancia fisica real: Rigidbody2D, rotura, fuerzas)
  Inventory/   ItemData (plantilla), InventorySystem (generico, jugador o NPC)
  Dialogue/    DialogueLine, DialogueSystem (conversacion activa)
  AI/          ActionIntent, ActionResult, IIntentInterpreter + RuleBasedIntentInterpreter,
               INPCResponder + RuleBasedNPCResponder, ActionExecutor (el motor)
  Powers/      PowerBase (contrato de cualquier poder), PowerController, TelekinesisPower
  SaveSystem/  SaveData (DTOs serializables), SaveManager (JSON en persistentDataPath)
  UI/          UIManager, ActionInputUI (la caja de texto libre), DialogueUI, StatsHUD
  Editor/      MVPSceneBuilder (genera la escena de la Fase 1 por codigo)
```

Cada sistema es independiente y se comunica con los demás solo a través de:
1. **Interfaces** (`IInteractable`, `IIntentInterpreter`, `INPCResponder`) para poder
   sustituir implementaciones sin tocar quien las usa.
2. **`EventBus`** (`RPG.Core`) para eventos que a varios sistemas les puede interesar
   (cambio de hora, un objeto se rompió, se registró un recuerdo...) sin acoplarlos entre sí.
3. **`GameManager`**, que mantiene las referencias compartidas (tiempo, diálogo, intérprete,
   ejecutor, guardado) accesibles vía `GameManager.Instance`.

No se usan `[CreateAssetMenu]` de más ni abstracciones especulativas: los `ScriptableObject`
(`NPCData`, `WorldObjectData`, `ItemData`) existen porque el diseño pide explícitamente poder
añadir NPCs/objetos/ítems **por datos**, sin tocar código.

## Cómo funciona una acción libre, paso a paso

Ejemplo: el jugador escribe `"Uso telequinesis para lanzar el sillon contra la pared."`

1. `ActionInputUI` lee el texto y llama a `GameManager.ProcessPlayerAction(texto)`.
2. `GameManager` arma un `ActionContext` con los nombres de las entidades cercanas
   (`PlayerInteractor.GetNearbyNames()`) y se lo pasa a `IIntentInterpreter.Interpret(...)`.
3. `RuleBasedIntentInterpreter` normaliza el texto, detecta la palabra clave "telequinesis"
   → `ActionType.UsePower`, detecta el sub-verbo "lanzar", y busca cuál de los nombres
   cercanos aparece en el texto → `TargetName = "Sillon"`.
4. `ActionExecutor.Execute(intent, actor)` resuelve `TargetName` a la instancia real
   (`PlayerInteractor.FindByName`) y, como el tipo es `UsePower`, delega en
   `PowerController.TryUsePower("telequinesis", ...)`.
5. `TelekinesisPower.Execute(...)` valida rango, energía, cooldown y peso vs. fuerza del
   jugador. Si es válido, gasta energía, aplica una fuerza física real
   (`Rigidbody2D.AddForce`) en la dirección en la que mira el jugador, y devuelve un
   `ActionResult` narrativo.
6. Si el sillón choca con la pared con suficiente fuerza, `WorldObject.OnCollisionEnter2D`
   lo rompe y emite un `WorldEvent` por el `EventBus`.
7. Cualquier `NPCController` cercano que esté escuchando ese evento decide si lo recuerda
   (`MemoryStore.Add`), sin que la IA ni el jugador hayan tocado su memoria directamente.
8. El resultado se muestra en la UI y queda registrado en el diario (`UIManager`).

Si en vez de eso el jugador escribe `"Levanto el edificio con mis manos."`, el intérprete
detecta el verbo "levanto" (`ActionType.Take`, sin poder de por medio) pero no hay ningún
objeto cercano llamado "edificio", así que `ActionExecutor` responde de forma natural
("No hay nada con ese nombre cerca de ti") en vez de inventar un resultado imposible. Si
"edificio" existiera como objeto del mundo, su peso simplemente superaría la fuerza base del
jugador y la respuesta sería "No tienes suficiente fuerza para...".

## Puntos de extensión pensados desde el principio

- **Nuevo poder** (telepatía, fuego, hielo...): crear una clase que herede de `PowerBase` y
  registrarla en `PowerController.Awake()`. Nada más cambia.
- **Nuevo objeto del mundo**: crear un asset `WorldObjectData` (o generarlo desde código como
  hace `MVPSceneBuilder`) y un `GameObject` con `WorldObject`. No requiere código nuevo.
- **Nuevo NPC**: crear un asset `NPCData` con su personalidad/trasfondo y un `GameObject` con
  `NPCController`. La memoria, emociones y relación son automáticas.
- **Nueva carrera/profesión**: en la Fase 1 `profession` es solo un dato en `NPCData`; el
  gameplay propio de cada carrera (Fase 3) se construirá como sistemas adicionales que leen
  ese mismo campo, sin modificar `NPCData` ni `NPCController`.
- **Intérprete real basado en IA/LLM**: implementar `IIntentInterpreter` (y `INPCResponder`)
  con una llamada a un modelo de lenguaje que devuelva la misma estructura `ActionIntent`.
  `ActionExecutor` sigue siendo la única autoridad sobre qué es válido ejecutar, así que un
  LLM nunca podría alterar estadísticas directamente aunque "alucine" — solo interpreta.

## Qué NO hace todavía este MVP (a propósito)

Siguiendo la instrucción de no construir todo a la vez, quedan fuera de la Fase 1 (y ya están
soportadas por el diseño, se añadirán en fases siguientes sin romper lo existente):

- Movimiento automático de NPCs siguiendo su rutina (`NPCRoutine` ya calcula el destino por
  hora, falta el `NavMeshAgent`/pathfinding 2D que los mueva).
- Economía completa (salarios, alquiler, bancos, deudas).
- Educación y carreras con minijuegos propios.
- Eventos dinámicos del mundo (incendios, fiestas, robos generados proceduralmente).
- Más poderes además de telequinesis.
- Un intérprete de lenguaje natural real (hoy es un sistema de reglas por palabras clave,
  suficiente para que el juego sea jugable offline en la Fase 1).

## Roadmap de fases (del documento de diseño original)

- **Fase 1 (este MVP)**: mapa pequeño, jugador, 5 NPCs, objetos físicos, diálogo, caja de
  texto libre, IA por reglas, telequinesis, memoria básica, guardado. ✅
- **Fase 2**: emociones más ricas, relaciones más profundas, rutinas con movimiento real,
  tiempo con más impacto en el mundo, economía básica.
- **Fase 3**: educación, carreras con gameplay propio, eventos dinámicos, inventario ampliado.
- **Fase 4**: poderes adicionales, mundo más grande, más NPCs y edificios.
- **Fase 5**: optimización, contenido, pulido, sonido, animaciones, menús, opciones, build
  para Windows.
