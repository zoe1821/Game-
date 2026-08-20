# Proyecto: RPG 2D de Roleplay Narrativo Libre

Un RPG 2D para PC (Unity) donde el jugador puede escribir **cualquier acción en texto libre**
("uso telequinesis para lanzar el sillón contra la pared", "le pregunto al profesor si puedo
quedarme después de clases") y el juego la interpreta y la ejecuta dentro de las reglas del
mundo — no un menú de opciones predefinidas.

Este repositorio contiene el **MVP de la Fase 1**: un mapa pequeño, el jugador, 5 NPCs con
memoria y personalidad, objetos físicos interactivos, diálogo, telequinesis y guardado/carga.
El resto de sistemas descritos en el diseño completo (economía, carreras, educación, rutinas
avanzadas, más poderes...) se construyen en fases posteriores sobre esta misma arquitectura,
ver [`ARCHITECTURE.md`](ARCHITECTURE.md).

## Requisitos

- **Unity 2022.3 LTS** (probado con 2022.3.21f1; cualquier 2022.3.x debería servir).
- No se necesitan paquetes externos: todo funciona con los módulos incluidos en Unity
  (2D Tilemap, UGUI, TextMeshPro) — ver `Packages/manifest.json`.

## Cómo abrir el proyecto

1. Abre Unity Hub → "Add" → selecciona la carpeta raíz de este repositorio.
2. Ábrelo con Unity 2022.3.x. Unity importará los paquetes automáticamente la primera vez.

## Cómo generar la escena jugable (solo la primera vez)

La escena de la Fase 1 no está guardada como archivo binario en el repositorio; se genera
**por código** para que sea 100% reproducible y fácil de revisar en el control de versiones
(en vez de un `.unity` gigante hecho a mano).

1. Con el proyecto abierto en el Editor, ve al menú **`RPG > Construir Escena MVP (Fase 1)`**.
2. Esto crea `Assets/_Project/Scenes/Phase1_MVP.unity` con el mapa, el jugador, los 5 NPCs,
   los objetos físicos, la UI y el `GameManager`, todos ya conectados.
3. Pulsa **Play**.

Puedes volver a ejecutar el mismo menú en cualquier momento para regenerar la escena desde
cero (por ejemplo tras modificar `MVPSceneBuilder.cs`).

## Controles

- **WASD / flechas**: moverse.
- **Caja de texto (abajo)**: escribe cualquier acción libre y pulsa Enter o "Enviar".
- **F5**: guardar partida. **F9**: cargar partida.

## Ejemplos de acciones libres para probar

```
Uso telequinesis para levantar la silla.
Uso telequinesis para lanzar el sillon contra la pared.
Le pregunto a Emily por que esta triste.
Le digo a Sarah que estoy mintiendo.
Robo el telefono de Sarah.
Empujo a John.
Me escondo.
Abro la puerta.
Rompo el sillon.
Levanto el edificio con mis manos.
```

La última debería fallar de forma natural ("No tienes suficiente fuerza..."), no inventar un
resultado imposible — esa es una regla central del diseño.

## Estado del proyecto

Ver [`ARCHITECTURE.md`](ARCHITECTURE.md) para el desglose completo de sistemas y el roadmap
de fases (estamos en la **Fase 1: MVP**).
