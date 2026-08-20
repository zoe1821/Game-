using System;
using UnityEngine;

namespace RPG.Player
{
    /// <summary>
    /// Estadisticas del jugador. Este es el UNICO lugar autorizado para modificar
    /// vida, energia, poder y dinero del jugador (regla: la IA interpreta, el motor ejecuta).
    /// </summary>
    public class PlayerStats : MonoBehaviour
    {
        [Header("Vida")]
        [SerializeField] private float maxHealth = 100f;
        [SerializeField] private float health = 100f;

        [Header("Energia (usada por los poderes)")]
        [SerializeField] private float maxEnergy = 100f;
        [SerializeField] private float energy = 100f;
        [SerializeField] private float energyRegenPerSecond = 4f;

        [Header("Economia")]
        [SerializeField] private float money = 50f;

        [Header("Poder")]
        [SerializeField] private int powerLevel = 1;
        [SerializeField] private float powerExperience = 0f;

        public float Health => health;
        public float MaxHealth => maxHealth;
        public float Energy => energy;
        public float MaxEnergy => maxEnergy;
        public float Money => money;
        public int PowerLevel => powerLevel;

        public event Action OnStatsChanged;

        private void Update()
        {
            if (energy < maxEnergy)
            {
                energy = Mathf.Min(maxEnergy, energy + energyRegenPerSecond * Time.deltaTime);
                OnStatsChanged?.Invoke();
            }
        }

        public void TakeDamage(float amount)
        {
            if (amount <= 0f) return;
            health = Mathf.Max(0f, health - amount);
            OnStatsChanged?.Invoke();
        }

        public void Heal(float amount)
        {
            if (amount <= 0f) return;
            health = Mathf.Min(maxHealth, health + amount);
            OnStatsChanged?.Invoke();
        }

        public bool HasEnoughEnergy(float amount) => energy >= amount;

        public bool TrySpendEnergy(float amount)
        {
            if (!HasEnoughEnergy(amount)) return false;
            energy -= amount;
            OnStatsChanged?.Invoke();
            return true;
        }

        public void AddMoney(float amount)
        {
            if (amount <= 0f) return;
            money += amount;
            OnStatsChanged?.Invoke();
        }

        public bool TrySpendMoney(float amount)
        {
            if (amount <= 0f) return true;
            if (money < amount) return false;
            money -= amount;
            OnStatsChanged?.Invoke();
            return true;
        }

        public void AddPowerExperience(float amount)
        {
            powerExperience += amount;
            float requiredForNextLevel = powerLevel * 100f;
            if (powerExperience >= requiredForNextLevel)
            {
                powerExperience -= requiredForNextLevel;
                powerLevel++;
            }
            OnStatsChanged?.Invoke();
        }

        public void LoadState(float loadedHealth, float loadedEnergy, float loadedMoney, int loadedPowerLevel, float loadedPowerXp)
        {
            health = loadedHealth;
            energy = loadedEnergy;
            money = loadedMoney;
            powerLevel = loadedPowerLevel;
            powerExperience = loadedPowerXp;
            OnStatsChanged?.Invoke();
        }
    }
}
