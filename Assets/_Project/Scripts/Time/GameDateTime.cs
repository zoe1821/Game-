using System;

namespace RPG.TimeSystem
{
    /// <summary>Representa la fecha/hora del mundo del juego (independiente del reloj real).</summary>
    [Serializable]
    public struct GameDateTime
    {
        public int Minute; // 0-59
        public int Hour;   // 0-23
        public int Day;    // 1-7 (dia de la semana)
        public int Week;   // semana del mes
        public int Month;  // 1-12
        public int Year;

        public static GameDateTime Default => new GameDateTime
        {
            Minute = 0,
            Hour = 7,
            Day = 1,
            Week = 1,
            Month = 1,
            Year = 1
        };

        public override string ToString() => $"Ano {Year}, Mes {Month}, Semana {Week}, Dia {Day} - {Hour:00}:{Minute:00}";
    }
}
