using System;
using System.Collections.Generic;
using System.Linq;

namespace RPG.NPC
{
    [Serializable]
    public class RoutineEntry
    {
        public int Hour;
        public string DestinationTag; // ej: "casa", "escuela", "parque"

        public RoutineEntry(int hour, string destinationTag)
        {
            Hour = hour;
            DestinationTag = destinationTag;
        }
    }

    /// <summary>
    /// Rutina diaria basica de un NPC. En la Fase 1 solo se usa para saber donde "deberia" estar
    /// un NPC segun la hora; el movimiento automatico completo llega en Fase 2. Las rutinas pueden
    /// sobreescribirse temporalmente por eventos (ej: una pelea hace que el NPC vaya a otro sitio).
    /// </summary>
    [Serializable]
    public class NPCRoutine
    {
        public List<RoutineEntry> Entries = new List<RoutineEntry>();
        private string _overrideDestination;

        public string GetDestinationForHour(int hour)
        {
            if (!string.IsNullOrEmpty(_overrideDestination))
                return _overrideDestination;

            var applicable = Entries.Where(e => e.Hour <= hour).OrderByDescending(e => e.Hour).FirstOrDefault();
            return applicable?.DestinationTag;
        }

        public void OverrideDestination(string destinationTag) => _overrideDestination = destinationTag;
        public void ClearOverride() => _overrideDestination = null;
    }
}
