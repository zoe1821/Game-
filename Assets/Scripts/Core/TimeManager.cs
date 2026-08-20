using System;
using UnityEngine;

namespace PsychHospital.Core
{
    /// Drives the hospital's day/hour clock. Every other simulated system (patient
    /// arrivals, future staff shifts, treatment schedules) reacts to this clock instead
    /// of real time, so speed changes and pausing affect the whole simulation uniformly.
    public class TimeManager : MonoBehaviour
    {
        private const float MinutesPerRealSecondAt1x = 10f;

        public int CurrentDay { get; private set; } = 1;
        public float CurrentHour { get; private set; } = 8f;
        public int SpeedMultiplier { get; private set; } = 1;
        public bool IsPaused { get; private set; }

        public event Action<int> OnDayChanged;
        public event Action<float> OnHourChanged;
        public event Action<int> OnSpeedChanged;

        private void Update()
        {
            if (IsPaused || SpeedMultiplier <= 0) return;

            float minutesElapsed = MinutesPerRealSecondAt1x * SpeedMultiplier * Time.deltaTime;
            CurrentHour += minutesElapsed / 60f;

            if (CurrentHour >= 24f)
            {
                CurrentHour -= 24f;
                CurrentDay++;
                OnDayChanged?.Invoke(CurrentDay);
            }

            OnHourChanged?.Invoke(CurrentHour);
        }

        public void SetSpeed(int multiplier)
        {
            SpeedMultiplier = Mathf.Clamp(multiplier, 0, 3);
            IsPaused = SpeedMultiplier == 0;
            OnSpeedChanged?.Invoke(SpeedMultiplier);
        }

        public void TogglePause()
        {
            IsPaused = !IsPaused;
            OnSpeedChanged?.Invoke(IsPaused ? 0 : SpeedMultiplier);
        }
    }
}
