using UnityEngine;
using RPG.AI;
using RPG.NPC;
using RPG.Player;
using RPG.World;

namespace RPG.Powers
{
    /// <summary>
    /// Primer poder completo del juego. Permite seleccionar, atraer, alejar, levantar,
    /// lanzar y empujar objetos y NPCs usando fisica 2D real (Rigidbody2D.AddForce).
    /// </summary>
    public class TelekinesisPower : PowerBase
    {
        private const float NpcApproxWeight = 65f;

        public TelekinesisPower()
        {
            PowerName = "telequinesis";
            EnergyCost = 12f;
            Range = 5f;
            Strength = 10f;
            Cooldown = 1.2f;
        }

        protected override void OnLevelUp()
        {
            Strength += 6f;
            Range += 0.5f;
            EnergyCost = Mathf.Max(6f, EnergyCost - 0.5f);
            Cooldown = Mathf.Max(0.4f, Cooldown - 0.1f);
        }

        public override ActionResult Execute(ActionIntent intent, GameObject actor, IInteractable target)
        {
            if (target == null)
                return ActionResult.Fail("No hay nada cerca a lo que apuntar con tu telequinesis.");

            if (IsOnCooldown)
                return ActionResult.Fail($"Tu telequinesis necesita {CooldownRemaining:0.0}s mas para recargarse.");

            var stats = actor.GetComponent<PlayerStats>();
            if (stats == null || !stats.HasEnoughEnergy(EnergyCost))
                return ActionResult.Fail("No tienes suficiente energia para usar telequinesis.");

            float distance = Vector2.Distance(actor.transform.position, target.Transform.position);
            if (distance > Range)
                return ActionResult.Fail($"{target.DisplayName} esta demasiado lejos para tu telequinesis.");

            Rigidbody2D body;
            float weight;
            bool isMovableFlag = true;

            switch (target)
            {
                case WorldObject obj:
                    body = obj.Body;
                    weight = obj.Data != null ? obj.Data.weight : 999f;
                    isMovableFlag = obj.Data == null || obj.Data.isMovable;
                    break;
                case NPCController:
                    body = target.Transform.GetComponent<Rigidbody2D>();
                    weight = NpcApproxWeight;
                    break;
                default:
                    return ActionResult.Fail("Tu telequinesis no tiene efecto sobre eso.");
            }

            if (body == null)
                return ActionResult.Fail($"{target.DisplayName} no se puede mover, parece fijo en su sitio.");

            if (!isMovableFlag)
                return ActionResult.Fail($"{target.DisplayName} esta fijado y no se puede mover.");

            if (weight > Strength)
                return ActionResult.Fail($"No tienes suficiente poder para mover algo tan pesado como {target.DisplayName}.");

            stats.TrySpendEnergy(EnergyCost);
            StartCooldown();

            string subVerb = string.IsNullOrEmpty(intent.Content) ? "levantar" : intent.Content;
            Vector2 toTarget = ((Vector2)target.Transform.position - (Vector2)actor.transform.position);
            Vector2 direction = toTarget.sqrMagnitude > 0.001f ? toTarget.normalized : Vector2.up;

            Vector2 force;
            string verbText;
            switch (subVerb)
            {
                case "lanzar":
                    Vector2 facing = actor.GetComponent<PlayerController>()?.FacingDirection ?? direction;
                    force = facing * Strength * 1.5f;
                    verbText = "lanzas";
                    break;
                case "empujar":
                    force = direction * Strength;
                    verbText = "empujas";
                    break;
                case "atraer":
                    force = -direction * Strength * 0.8f;
                    verbText = "atraes";
                    break;
                default: // levantar / suspender
                    force = Vector2.up * Strength * 0.9f;
                    verbText = "levantas";
                    break;
            }

            body.AddForce(force, ForceMode2D.Impulse);
            AddExperience(5f);

            var result = ActionResult.Ok($"Con telequinesis, {verbText} {target.DisplayName}.");

            if (target is NPCController npc)
                npc.ReactTo(intent, result);

            return result;
        }
    }
}
