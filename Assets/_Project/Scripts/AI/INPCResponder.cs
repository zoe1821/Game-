using RPG.NPC;

namespace RPG.AI
{
    /// <summary>
    /// Genera la linea de dialogo/reaccion de un NPC ante una accion del jugador ya validada
    /// por el motor. Al igual que IIntentInterpreter, esta abstraccion permite sustituir la
    /// implementacion base por reglas por una impulsada por un modelo de lenguaje en el futuro.
    /// </summary>
    public interface INPCResponder
    {
        string GenerateResponse(NPCController npc, ActionIntent intent, ActionResult result);
    }
}
