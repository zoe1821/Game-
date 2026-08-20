using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace RPG.Inventory
{
    [Serializable]
    public class InventoryEntry
    {
        public ItemData Item;
        public int Quantity;

        public InventoryEntry(ItemData item, int quantity)
        {
            Item = item;
            Quantity = quantity;
        }
    }

    /// <summary>
    /// Inventario generico reutilizable por el jugador o cualquier NPC.
    /// Es el unico sistema autorizado para anadir/quitar objetos de un portador.
    /// </summary>
    public class InventorySystem : MonoBehaviour
    {
        [SerializeField] private float maxWeight = 40f;
        [SerializeField] private List<InventoryEntry> entries = new List<InventoryEntry>();

        public IReadOnlyList<InventoryEntry> Entries => entries;
        public float MaxWeight => maxWeight;
        public float CurrentWeight => entries.Sum(e => e.Item.weight * e.Quantity);

        public event Action OnInventoryChanged;

        public bool HasItem(string itemId, int quantity = 1)
        {
            var entry = entries.FirstOrDefault(e => e.Item.itemId == itemId);
            return entry != null && entry.Quantity >= quantity;
        }

        public bool TryAddItem(ItemData item, int quantity = 1)
        {
            if (item == null || quantity <= 0) return false;
            if (CurrentWeight + item.weight * quantity > maxWeight) return false;

            var existing = item.stackable ? entries.FirstOrDefault(e => e.Item == item) : null;
            if (existing != null)
            {
                existing.Quantity = Mathf.Min(existing.Quantity + quantity, item.maxStack);
            }
            else
            {
                entries.Add(new InventoryEntry(item, quantity));
            }

            OnInventoryChanged?.Invoke();
            return true;
        }

        public bool TryRemoveItem(ItemData item, int quantity = 1)
        {
            var existing = entries.FirstOrDefault(e => e.Item == item);
            if (existing == null || existing.Quantity < quantity) return false;

            existing.Quantity -= quantity;
            if (existing.Quantity <= 0) entries.Remove(existing);

            OnInventoryChanged?.Invoke();
            return true;
        }

        public void LoadState(List<InventoryEntry> loadedEntries)
        {
            entries = loadedEntries ?? new List<InventoryEntry>();
            OnInventoryChanged?.Invoke();
        }
    }
}
