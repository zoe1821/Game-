using UnityEngine;
using UnityEngine.UI;
using RPG.Player;
using RPG.TimeSystem;

namespace RPG.UI
{
    /// <summary>HUD con vida, energia, poder, dinero y hora del mundo.</summary>
    public class StatsHUD : MonoBehaviour
    {
        [SerializeField] private PlayerStats playerStats;
        [SerializeField] private TimeManager timeManager;

        [SerializeField] private Slider healthSlider;
        [SerializeField] private Slider energySlider;
        [SerializeField] private Text moneyText;
        [SerializeField] private Text powerLevelText;
        [SerializeField] private Text timeText;

        private void Start()
        {
            if (playerStats != null) playerStats.OnStatsChanged += Refresh;
            Refresh();
        }

        private void OnDestroy()
        {
            if (playerStats != null) playerStats.OnStatsChanged -= Refresh;
        }

        private void Update()
        {
            if (timeText != null && timeManager != null)
                timeText.text = $"{timeManager.Current.Hour:00}:{timeManager.Current.Minute:00} - Dia {timeManager.Current.Day}";
        }

        private void Refresh()
        {
            if (playerStats == null) return;

            if (healthSlider != null)
            {
                healthSlider.maxValue = playerStats.MaxHealth;
                healthSlider.value = playerStats.Health;
            }
            if (energySlider != null)
            {
                energySlider.maxValue = playerStats.MaxEnergy;
                energySlider.value = playerStats.Energy;
            }
            if (moneyText != null) moneyText.text = $"${playerStats.Money:0}";
            if (powerLevelText != null) powerLevelText.text = $"Poder Nv.{playerStats.PowerLevel}";
        }
    }
}
