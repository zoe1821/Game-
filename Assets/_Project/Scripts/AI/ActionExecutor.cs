using UnityEngine;
using RPG.Core;
using RPG.Dialogue;
using RPG.Inventory;
using RPG.NPC;
using RPG.Player;
using RPG.Powers;
using RPG.World;

namespace RPG.AI
{
    /// <summary>
    /// El motor del juego. Recibe una ActionIntent YA interpretada y decide si es posible
    /// ejecutarla; si lo es, es el UNICO responsable de modificar estadisticas, inventario,
    /// posiciones, memoria de NPCs, etc. La IA (interpretador) nunca toca estos sistemas
    /// directamente, solo produce la intencion.
    /// </summary>
    public class ActionExecutor
    {
        private const float PlayerBaseStrengthKg = 6f;   // fuerza sin usar poderes
        private const float PushForceMagnitude = 4f;
        private const float BodyActionEnergyCost = 2f;

        private readonly PlayerStats _playerStats;
        private readonly PlayerInteractor _playerInteractor;
        private readonly InventorySystem _playerInventory;
        private readonly PowerController _powerController;
        private readonly DialogueSystem _dialogue;

        public ActionExecutor(PlayerStats playerStats, PlayerInteractor playerInteractor,
            InventorySystem playerInventory, PowerController powerController, DialogueSystem dialogue)
        {
            _playerStats = playerStats;
            _playerInteractor = playerInteractor;
            _playerInventory = playerInventory;
            _powerController = powerController;
            _dialogue = dialogue;
        }

        public ActionResult Execute(ActionIntent intent, GameObject actor)
        {
            IInteractable target = string.IsNullOrEmpty(intent.TargetName)
                ? null
                : _playerInteractor.FindByName(intent.TargetName);

            ActionResult result = intent.Type switch
            {
                ActionType.Talk => ExecuteSocial(intent, target),
                ActionType.Ask => ExecuteSocial(intent, target),
                ActionType.Lie => ExecuteSocial(intent, target),
                ActionType.Help => ExecuteSocial(intent, target),

                ActionType.Steal => ExecuteSteal(intent, target),
                ActionType.Take => ExecuteTake(intent, target),
                ActionType.Drop => ActionResult.Ok("Sueltas el objeto en el suelo."),

                ActionType.Push => ExecutePush(intent, actor, target),
                ActionType.Throw => ExecuteThrow(intent, actor, target),
                ActionType.Attack => ExecuteAttack(intent, target),

                ActionType.Break => ExecuteBreak(target),
                ActionType.Open => ExecuteToggleUsable(target, "Abres"),
                ActionType.Close => ExecuteToggleUsable(target, "Cierras"),
                ActionType.Use => ExecuteToggleUsable(target, "Usas"),

                ActionType.UsePower => ExecutePower(intent, actor, target),

                ActionType.Hide => ExecuteBodyAction("Te escondes. Esperas en silencio."),
                ActionType.Run => ExecuteBodyAction("Corres."),
                ActionType.Escape => ExecuteBodyAction("Sales corriendo de alli."),
                ActionType.Jump => ExecuteBodyAction("Saltas."),
                ActionType.Sit => ExecuteBodyAction("Te sientas."),
                ActionType.LieDown => ExecuteBodyAction("Te acuestas."),
                ActionType.Move => ActionResult.Ok("Te mueves hacia alli."),

                _ => ActionResult.Fail("No entiendes bien como hacer eso. Intenta describirlo de otra forma.")
            };

            if (result.Success)
                EventBus.RaiseJournalEntry(result.Message);

            return result;
        }

        private ActionResult ExecuteSocial(ActionIntent intent, IInteractable target)
        {
            if (target is not NPCController npc)
                return ActionResult.Fail("No hay nadie con ese nombre cerca de ti.");

            if (!_dialogue.IsInConversation || _dialogue.CurrentPartner != npc)
                _dialogue.StartConversation(npc);

            _dialogue.AddPlayerLine(intent.Content ?? intent.RawText);

            var ok = ActionResult.Ok($"Hablas con {npc.DisplayName}.");
            string response = npc.ReactTo(intent, ok);
            return ActionResult.Ok(response);
        }

        private ActionResult ExecuteSteal(ActionIntent intent, IInteractable target)
        {
            if (target is NPCController)
                return ActionResult.Fail("No puedes robarle directamente a una persona asi, prueba con un objeto suyo.");

            if (target is not WorldObject obj)
                return ActionResult.Fail("No hay nada con ese nombre cerca de ti.");

            if (string.IsNullOrEmpty(obj.OwnerId))
                return ExecuteTake(intent, target); // nadie es dueno: no es robo, es solo tomarlo

            if (obj.Data == null || !obj.Data.isPickable)
                return ActionResult.Fail($"No puedes llevarte {obj.DisplayName}.");

            string ownerId = obj.OwnerId;
            obj.OwnerId = "player";
            TryGiveItemToPlayer(obj);

            var result = ActionResult.Ok($"Robas {obj.DisplayName}.");

            foreach (var interactable in _playerInteractor.GetNearbyInteractables())
            {
                if (interactable is NPCController npc && npc.Data != null && npc.Data.npcId == ownerId)
                    npc.ReactTo(intent, result, "player");
            }

            return result;
        }

        private ActionResult ExecuteTake(ActionIntent intent, IInteractable target)
        {
            if (target is not WorldObject obj)
                return ActionResult.Fail("No hay nada con ese nombre cerca de ti.");

            if (obj.Data == null || !obj.Data.isPickable)
                return ActionResult.Fail($"No puedes llevarte {obj.DisplayName}, es demasiado grande o no se puede recoger.");

            if (!TryGiveItemToPlayer(obj))
                return ActionResult.Fail("No tienes espacio suficiente en tu inventario.");

            return ActionResult.Ok($"Recoges {obj.DisplayName}.");
        }

        private bool TryGiveItemToPlayer(WorldObject obj)
        {
            if (obj.Data.correspondingItem != null)
            {
                if (!_playerInventory.TryAddItem(obj.Data.correspondingItem, 1))
                    return false;
            }
            obj.gameObject.SetActive(false);
            return true;
        }

        private ActionResult ExecutePush(ActionIntent intent, GameObject actor, IInteractable target)
        {
            if (target == null)
                return ActionResult.Fail("No hay nada ni nadie con ese nombre cerca de ti para empujar.");

            if (target is WorldObject obj)
            {
                Vector2 direction = ((Vector2)obj.Transform.position - (Vector2)actor.transform.position).normalized;
                bool moved = obj.TryApplyForce(direction * PushForceMagnitude, PlayerBaseStrengthKg);
                return moved
                    ? ActionResult.Ok($"Empujas {obj.DisplayName}.")
                    : ActionResult.Fail($"No tienes suficiente fuerza para mover {obj.DisplayName}.");
            }

            if (target is NPCController npc)
            {
                var result = ActionResult.Ok($"Empujas a {npc.DisplayName}.");
                npc.ReactTo(intent, result);
                return result;
            }

            return ActionResult.Fail("No puedes empujar eso.");
        }

        private ActionResult ExecuteThrow(ActionIntent intent, GameObject actor, IInteractable target)
        {
            // Sin un poder de por medio, lanzar algo requiere que sea ligero.
            if (target is not WorldObject obj)
                return ActionResult.Fail("No hay nada con ese nombre cerca de ti.");

            if (obj.Data == null || obj.Data.weight > PlayerBaseStrengthKg)
                return ActionResult.Fail($"No tienes suficiente fuerza para lanzar {obj.DisplayName} con tus manos.");

            Vector2 direction = actor.GetComponent<PlayerController>()?.FacingDirection ?? Vector2.right;
            obj.TryApplyForce(direction * PushForceMagnitude * 2f, PlayerBaseStrengthKg);
            return ActionResult.Ok($"Lanzas {obj.DisplayName}.");
        }

        private ActionResult ExecuteAttack(ActionIntent intent, IInteractable target)
        {
            if (target is NPCController npc)
            {
                var result = ActionResult.Ok($"Atacas a {npc.DisplayName}.");
                npc.ReactTo(intent, result);
                return result;
            }

            if (target is WorldObject obj)
                return ExecuteBreak(obj);

            return ActionResult.Fail("No hay nada ni nadie con ese nombre cerca de ti para atacar.");
        }

        private ActionResult ExecuteBreak(IInteractable target)
        {
            if (target is not WorldObject obj)
                return ActionResult.Fail("No hay nada con ese nombre cerca de ti.");

            if (obj.Data == null || !obj.Data.isDestructible)
                return ActionResult.Fail($"{obj.DisplayName} no se puede romper.");

            obj.Break();
            return ActionResult.Ok($"Rompes {obj.DisplayName}.");
        }

        private ActionResult ExecuteToggleUsable(IInteractable target, string verb)
        {
            if (target is not WorldObject obj)
                return ActionResult.Fail("No hay nada con ese nombre cerca de ti.");

            if (obj.Data == null || (!obj.Data.isUsable && verb == "Usas"))
                return ActionResult.Fail($"No puedes usar {obj.DisplayName}.");

            return ActionResult.Ok($"{verb} {obj.DisplayName}.");
        }

        private ActionResult ExecutePower(ActionIntent intent, GameObject actor, IInteractable target)
        {
            if (_powerController == null)
                return ActionResult.Fail("Todavia no tienes ningun poder.");

            return _powerController.TryUsePower(intent.PowerName, intent, actor, target);
        }

        private ActionResult ExecuteBodyAction(string message)
        {
            _playerStats.TrySpendEnergy(BodyActionEnergyCost);
            return ActionResult.Ok(message);
        }
    }
}
