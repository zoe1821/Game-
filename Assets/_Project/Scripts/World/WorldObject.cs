using UnityEngine;
using RPG.AI;
using RPG.Core;

namespace RPG.World
{
    public enum WorldObjectState { Normal, Broken, OnFire }

    /// <summary>
    /// Instancia real de un objeto del mundo con fisica (Rigidbody2D). Puede ser movido,
    /// lanzado, roto o recogido. Este componente es el unico que modifica el estado fisico
    /// del objeto: la IA nunca decide directamente si algo se rompe o se mueve.
    /// </summary>
    [RequireComponent(typeof(Collider2D))]
    public class WorldObject : MonoBehaviour, IInteractable
    {
        [SerializeField] private string objectId = "";
        [SerializeField] private WorldObjectData data;
        [SerializeField] private WorldObjectState state = WorldObjectState.Normal;
        [SerializeField] private string ownerId = ""; // vacio = sin dueno

        private Rigidbody2D _rb;

        public string ObjectId => string.IsNullOrEmpty(objectId) ? gameObject.name : objectId;
        public WorldObjectData Data => data;
        public WorldObjectState State { get => state; private set => state = value; }
        public string OwnerId { get => ownerId; set => ownerId = value; }
        public Rigidbody2D Body => _rb;

        public string DisplayName => data != null ? data.objectName : gameObject.name;
        public Transform Transform => transform;

        private void Awake()
        {
            _rb = GetComponent<Rigidbody2D>();
        }

        public bool CanInteract(GameObject actor) => state != WorldObjectState.Broken;

        /// <summary>Interaccion generica (recoger/usar). Las acciones de fuerza (empujar, lanzar) las gestiona el sistema de Poderes.</summary>
        public ActionResult Interact(GameObject actor, ActionIntent intent)
        {
            if (!CanInteract(actor))
                return ActionResult.Fail($"{DisplayName} esta roto y no se puede usar.");

            switch (intent.Type)
            {
                case ActionType.Take:
                    if (data == null || !data.isPickable)
                        return ActionResult.Fail($"No puedes llevarte {DisplayName}, es demasiado grande o no es tuyo para tomarlo.");
                    return ActionResult.Ok($"Recoges {DisplayName}.");

                case ActionType.UsePower:
                default:
                    return ActionResult.Ok($"Interactuas con {DisplayName}.");
            }
        }

        /// <summary>Usado por la telequinesis y por empujones fisicos del jugador/NPC.</summary>
        public bool TryApplyForce(Vector2 force, float actorStrength)
        {
            if (_rb == null || data == null || !data.isMovable) return false;
            if (data.weight > actorStrength) return false;

            _rb.AddForce(force, ForceMode2D.Impulse);
            return true;
        }

        public void Break()
        {
            if (state == WorldObjectState.Broken) return;
            state = WorldObjectState.Broken;
            EventBus.RaiseJournalEntry($"{DisplayName} se ha roto.");
        }

        public void LoadState(WorldObjectState loadedState, string loadedOwnerId, Vector2 position)
        {
            state = loadedState;
            ownerId = loadedOwnerId ?? "";
            if (_rb != null) _rb.position = position;
            else transform.position = position;
        }

        private void OnCollisionEnter2D(Collision2D collision)
        {
            if (data == null || !data.isDestructible || state == WorldObjectState.Broken) return;

            float impactMagnitude = collision.relativeVelocity.magnitude;
            if (impactMagnitude >= data.destructionImpactThreshold)
            {
                Break();
                EventBus.RaiseWorldEvent(new WorldEvent(
                    $"{DisplayName} se rompio con un fuerte impacto.",
                    transform.position,
                    6f,
                    ownerId));
            }
        }
    }
}
