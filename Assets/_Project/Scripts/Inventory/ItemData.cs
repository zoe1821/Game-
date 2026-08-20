using UnityEngine;

namespace RPG.Inventory
{
    /// <summary>Plantilla de un objeto que puede existir dentro de un inventario.</summary>
    [CreateAssetMenu(fileName = "NewItem", menuName = "RPG/Inventory/Item Data")]
    public class ItemData : ScriptableObject
    {
        public string itemId;
        public string itemName = "Objeto";
        [TextArea] public string description = "";
        public float weight = 1f;
        public float value = 0f;
        public bool stackable = true;
        public int maxStack = 20;
        public Color placeholderColor = Color.white; // hasta que existan sprites de arte
    }
}
