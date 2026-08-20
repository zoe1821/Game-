using UnityEngine;
using RPG.AI;

namespace RPG.World
{
    /// <summary>
    /// Contrato comun para cualquier entidad del mundo con la que el jugador (o un NPC)
    /// pueda interactuar: NPCs, objetos, puertas, etc.
    /// </summary>
    public interface IInteractable
    {
        string DisplayName { get; }
        Transform Transform { get; }
        bool CanInteract(GameObject actor);

        /// <summary>Ejecuta la interaccion ya validada por el ActionExecutor y devuelve el resultado narrativo.</summary>
        ActionResult Interact(GameObject actor, ActionIntent intent);
    }
}
