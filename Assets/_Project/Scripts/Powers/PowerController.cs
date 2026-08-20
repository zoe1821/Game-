using System.Collections.Generic;
using UnityEngine;
using RPG.AI;
using RPG.World;

namespace RPG.Powers
{
    /// <summary>
    /// Contenedor de los poderes que posee una entidad (normalmente el jugador).
    /// Anadir un poder nuevo (telepatia, fuego...) solo requiere registrar aqui una
    /// nueva instancia de PowerBase; ningun otro sistema necesita cambiar.
    /// </summary>
    public class PowerController : MonoBehaviour
    {
        private readonly Dictionary<string, PowerBase> _powers = new Dictionary<string, PowerBase>();

        private void Awake()
        {
            RegisterPower(new TelekinesisPower());
        }

        private void Update()
        {
            foreach (var power in _powers.Values)
                power.Tick(Time.deltaTime);
        }

        public void RegisterPower(PowerBase power) => _powers[power.PowerName] = power;

        public bool HasPower(string powerName) => !string.IsNullOrEmpty(powerName) && _powers.ContainsKey(powerName);

        public PowerBase GetPower(string powerName) => _powers.TryGetValue(powerName ?? "", out var p) ? p : null;

        public ActionResult TryUsePower(string powerName, ActionIntent intent, GameObject actor, IInteractable target)
        {
            var power = GetPower(powerName);
            if (power == null)
                return ActionResult.Fail("No tienes ese poder.");

            return power.Execute(intent, actor, target);
        }
    }
}
