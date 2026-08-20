using UnityEngine;
using RPG.Inventory;

namespace RPG.World
{
    /// <summary>
    /// Plantilla de datos de un tipo de objeto del mundo (silla, mesa, telefono...).
    /// Permite anadir nuevos objetos por datos, sin tocar codigo.
    /// </summary>
    [CreateAssetMenu(fileName = "NewWorldObject", menuName = "RPG/World/World Object Data")]
    public class WorldObjectData : ScriptableObject
    {
        public string objectName = "Objeto";
        [TextArea] public string description = "";

        [Header("Propiedades fisicas")]
        public float weight = 5f;         // kg aproximados, usado por telequinesis y fuerza del jugador
        public bool isMovable = true;
        public bool isDestructible = false;
        public bool isPickable = false;   // puede pasar al inventario
        public bool isUsable = false;     // tiene una accion de "usar" (ej: telefono, computadora)

        [Header("Inventario (solo si isPickable)")]
        [Tooltip("Item que se anade al inventario cuando este objeto se recoge del mundo.")]
        public ItemData correspondingItem;

        [Header("Economia")]
        public float baseValue = 0f;

        [Header("Umbral de dano por impacto (si es destructible)")]
        public float destructionImpactThreshold = 8f;
    }
}
