using UnityEngine;
using RPG.Core;

namespace RPG.TimeSystem
{
    /// <summary>
    /// Controla el paso del tiempo del mundo (minuto -> hora -> dia -> semana -> mes -> anio).
    /// Las rutinas de los NPC y los eventos dependen de este reloj. Solo este sistema puede
    /// modificar el tiempo del juego.
    /// </summary>
    public class TimeManager : MonoBehaviour
    {
        [Tooltip("Cuantos minutos de juego avanzan por segundo real.")]
        [SerializeField] private float gameMinutesPerRealSecond = 2f;
        [SerializeField] private bool isPaused = false;

        public GameDateTime Current { get; private set; } = GameDateTime.Default;

        private float _accumulator;

        public bool IsPaused
        {
            get => isPaused;
            set => isPaused = value;
        }

        private void Update()
        {
            if (isPaused) return;

            _accumulator += Time.deltaTime * gameMinutesPerRealSecond;
            while (_accumulator >= 1f)
            {
                _accumulator -= 1f;
                AdvanceMinutes(1);
            }
        }

        public void AdvanceMinutes(int minutes)
        {
            GameDateTime t = Current;
            int previousHour = t.Hour;
            int previousDay = t.Day;

            t.Minute += minutes;
            while (t.Minute >= 60)
            {
                t.Minute -= 60;
                t.Hour++;
            }
            while (t.Hour >= 24)
            {
                t.Hour -= 24;
                t.Day++;
            }
            while (t.Day > 7)
            {
                t.Day -= 7;
                t.Week++;
            }
            while (t.Week > 4)
            {
                t.Week -= 4;
                t.Month++;
            }
            while (t.Month > 12)
            {
                t.Month -= 12;
                t.Year++;
            }

            Current = t;

            if (t.Hour != previousHour)
                EventBus.RaiseHourChanged(t.Hour);
            if (t.Day != previousDay)
                EventBus.RaiseDayChanged(t.Day);
        }

        public void LoadState(GameDateTime state) => Current = state;
    }
}
