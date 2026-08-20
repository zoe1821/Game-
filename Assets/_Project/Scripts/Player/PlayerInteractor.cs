using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using RPG.World;

namespace RPG.Player
{
    /// <summary>
    /// Detecta que entidades interactuables (NPCs, objetos) estan cerca del jugador.
    /// El ActionExecutor usa esta lista para resolver a que se refiere el jugador
    /// cuando escribe una accion libre ("la silla", "Sarah", "la puerta"...).
    /// </summary>
    public class PlayerInteractor : MonoBehaviour
    {
        [SerializeField] private float interactionRadius = 3.5f;
        [SerializeField] private LayerMask interactableMask = ~0;

        public float InteractionRadius => interactionRadius;

        public List<IInteractable> GetNearbyInteractables()
        {
            var results = new List<IInteractable>();
            var hits = Physics2D.OverlapCircleAll(transform.position, interactionRadius, interactableMask);
            foreach (var hit in hits)
            {
                var interactable = hit.GetComponentInParent<IInteractable>();
                if (interactable != null && !results.Contains(interactable))
                    results.Add(interactable);
            }
            return results;
        }

        public IEnumerable<string> GetNearbyNames() => GetNearbyInteractables().Select(i => i.DisplayName);

        public IInteractable FindByName(string name)
        {
            if (string.IsNullOrWhiteSpace(name)) return null;
            string normalized = name.Trim().ToLowerInvariant();
            return GetNearbyInteractables()
                .FirstOrDefault(i => i.DisplayName.ToLowerInvariant().Contains(normalized)
                                      || normalized.Contains(i.DisplayName.ToLowerInvariant()));
        }

        private void OnDrawGizmosSelected()
        {
            Gizmos.color = new Color(0.2f, 0.9f, 1f, 0.35f);
            Gizmos.DrawWireSphere(transform.position, interactionRadius);
        }
    }
}
