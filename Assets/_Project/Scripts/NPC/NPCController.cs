using UnityEngine;
using RPG.AI;
using RPG.Core;
using RPG.Memory;
using RPG.World;

namespace RPG.NPC
{
    /// <summary>
    /// Entidad NPC completa: combina la plantilla (NPCData), el estado en vivo (NPCState),
    /// su memoria persistente y su rutina. Reacciona a las acciones del jugador ya validadas
    /// por el ActionExecutor: nunca decide por si mismo cambios de inventario/dinero/posicion del jugador.
    /// </summary>
    public class NPCController : MonoBehaviour, IInteractable
    {
        [SerializeField] private NPCData data;
        [SerializeField] private NPCRoutine routine = new NPCRoutine();

        public NPCState State { get; private set; } = new NPCState();
        public MemoryStore Memory { get; } = new MemoryStore();
        public NPCData Data => data;
        public NPCRoutine Routine => routine;

        public string DisplayName => data != null ? data.npcName : gameObject.name;
        public Transform Transform => transform;

        private void Awake()
        {
            if (data != null)
                State.Money = data.startingMoney;
        }

        private void OnEnable() => EventBus.OnWorldEvent += HandleWorldEvent;
        private void OnDisable() => EventBus.OnWorldEvent -= HandleWorldEvent;

        /// <summary>Si el NPC esta lo bastante cerca de un suceso perceptible (un golpe, una rotura...), lo recuerda.</summary>
        private void HandleWorldEvent(WorldEvent worldEvent)
        {
            if (worldEvent.ActorId == (data != null ? data.npcId : DisplayName)) return;

            float distance = Vector2.Distance(transform.position, worldEvent.Position);
            if (distance > worldEvent.Radius) return;

            string description = $"{DisplayName} presencio: {worldEvent.Description}";
            var entry = new MemoryEntry(
                description,
                GameManager.Instance != null ? GameManager.Instance.Time.Current : default,
                new[] { data != null ? data.npcId : DisplayName },
                -0.1f,
                new[] { "presenciado" });

            Memory.Add(entry);
            State.SetEmotion(EmotionType.Surprise, 0.5f);
        }

        public bool CanInteract(GameObject actor) => true;

        public void LoadRuntimeState(NPCState loadedState, System.Collections.Generic.IEnumerable<MemoryEntry> memories, Vector2 position)
        {
            State = loadedState ?? new NPCState();
            if (memories != null) Memory.LoadEntries(memories);
            transform.position = position;
        }

        public ActionResult Interact(GameObject actor, ActionIntent intent)
        {
            var gm = GameManager.Instance;
            if (gm == null) return ActionResult.Fail("El mundo no esta listo todavia.");

            gm.Dialogue.StartConversation(this);
            string opening = gm.NpcResponder.GenerateResponse(this, intent, ActionResult.Ok("saludo"));
            gm.Dialogue.AddNpcLine(DisplayName, opening);
            return ActionResult.Ok(opening);
        }

        /// <summary>
        /// Reaccion del NPC ante una accion del jugador ya ejecutada por el motor
        /// (por ejemplo, que le hayan empujado o robado algo). Actualiza emocion, relacion y memoria.
        /// </summary>
        public string ReactTo(ActionIntent intent, ActionResult result, string actorId = "player")
        {
            ApplyEmotionalReaction(intent, result);
            RecordMemory(intent, result, actorId);

            var gm = GameManager.Instance;
            string line = gm != null ? gm.NpcResponder.GenerateResponse(this, intent, result) : result.Message;

            if (gm != null && gm.Dialogue.IsInConversation && gm.Dialogue.CurrentPartner == this)
                gm.Dialogue.AddNpcLine(DisplayName, line);

            return line;
        }

        private void ApplyEmotionalReaction(ActionIntent intent, ActionResult result)
        {
            if (!result.Success) return;

            switch (intent.Type)
            {
                case ActionType.Steal:
                    State.SetEmotion(EmotionType.Anger, 0.8f);
                    State.ApplyRelationshipDelta(-25f);
                    break;
                case ActionType.Push:
                case ActionType.Attack:
                    State.SetEmotion(EmotionType.Fear, 0.7f);
                    State.ApplyRelationshipDelta(-15f);
                    break;
                case ActionType.Lie:
                    State.SetEmotion(EmotionType.Distrust, 0.5f);
                    State.ApplyRelationshipDelta(-8f);
                    break;
                case ActionType.Help:
                    State.SetEmotion(EmotionType.Happy, 0.6f);
                    State.ApplyRelationshipDelta(10f);
                    break;
                case ActionType.Ask:
                case ActionType.Talk:
                    State.SetEmotion(EmotionType.Trust, 0.3f);
                    State.ApplyRelationshipDelta(2f);
                    break;
                case ActionType.UsePower:
                    State.SetEmotion(EmotionType.Surprise, 0.9f);
                    State.ApplyRelationshipDelta(-5f);
                    break;
            }
        }

        private void RecordMemory(ActionIntent intent, ActionResult result, string actorId)
        {
            if (!result.Success) return;

            string description = $"{DisplayName} recuerda que {actorId} {DescribeAction(intent)}.";
            var entry = new MemoryEntry(
                description,
                GameManager.Instance != null ? GameManager.Instance.Time.Current : default,
                new[] { actorId, data != null ? data.npcId : DisplayName },
                EstimateEmotionalWeight(intent),
                new[] { intent.Type.ToString().ToLowerInvariant() });

            Memory.Add(entry);
            EventBus.RaiseMemoryRecorded(data != null ? data.npcId : DisplayName, description);
        }

        private static string DescribeAction(ActionIntent intent) => intent.Type switch
        {
            ActionType.Steal => "le robo algo",
            ActionType.Push => "lo empujo",
            ActionType.Attack => "lo ataco",
            ActionType.Lie => "le mintio",
            ActionType.Help => "lo ayudo",
            ActionType.UsePower => "uso un poder cerca de el/ella",
            _ => "interactuo con el/ella"
        };

        private static float EstimateEmotionalWeight(ActionIntent intent) => intent.Type switch
        {
            ActionType.Steal => -0.8f,
            ActionType.Push or ActionType.Attack => -0.6f,
            ActionType.Lie => -0.3f,
            ActionType.Help => 0.6f,
            ActionType.Ask or ActionType.Talk => 0.1f,
            _ => 0f
        };
    }
}
