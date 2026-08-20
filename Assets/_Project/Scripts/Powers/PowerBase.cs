using UnityEngine;
using RPG.AI;
using RPG.World;

namespace RPG.Powers
{
    /// <summary>
    /// Base para cualquier poder sobrenatural (telequinesis, y en el futuro telepatia,
    /// invisibilidad, fuego, hielo, electricidad, curacion, supervelocidad...).
    /// Cada poder controla su propio coste, alcance, fuerza, precision, velocidad,
    /// cooldown y experiencia; el motor (ActionExecutor) solo le delega la ejecucion.
    /// </summary>
    public abstract class PowerBase
    {
        public string PowerName { get; protected set; }
        public int Level { get; protected set; } = 1;
        public float Experience { get; protected set; }

        public float EnergyCost { get; protected set; } = 10f;
        public float Range { get; protected set; } = 5f;
        public float Strength { get; protected set; } = 8f;   // kg maximos que puede mover al nivel actual
        public float Precision { get; protected set; } = 0.8f;
        public float Speed { get; protected set; } = 1f;
        public float Cooldown { get; protected set; } = 1.5f;

        private float _cooldownRemaining;
        public bool IsOnCooldown => _cooldownRemaining > 0f;
        public float CooldownRemaining => _cooldownRemaining;

        public void Tick(float deltaTime)
        {
            if (_cooldownRemaining > 0f)
                _cooldownRemaining = Mathf.Max(0f, _cooldownRemaining - deltaTime);
        }

        protected void StartCooldown() => _cooldownRemaining = Cooldown;

        public void AddExperience(float amount)
        {
            Experience += amount;
            float requiredForNextLevel = Level * 50f;
            if (Experience >= requiredForNextLevel)
            {
                Experience -= requiredForNextLevel;
                Level++;
                OnLevelUp();
            }
        }

        /// <summary>Aumenta las capacidades del poder al subir de nivel. Cada poder define su propia progresion.</summary>
        protected abstract void OnLevelUp();

        public abstract ActionResult Execute(ActionIntent intent, GameObject actor, IInteractable target);
    }
}
