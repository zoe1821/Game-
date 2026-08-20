using System;
using RPG.TimeSystem;

namespace RPG.Memory
{
    /// <summary>Un recuerdo individual guardado por un NPC.</summary>
    [Serializable]
    public class MemoryEntry
    {
        public string Description;      // "El jugador me robo el telefono."
        public GameDateTime Timestamp;
        public string[] InvolvedActors; // ids: "player", "npc_sarah"...
        public float EmotionalWeight;   // -1 (muy negativo) a +1 (muy positivo)
        public string[] Tags;           // "robo", "violencia", "amabilidad"...

        public MemoryEntry(string description, GameDateTime timestamp, string[] involvedActors, float emotionalWeight, string[] tags)
        {
            Description = description;
            Timestamp = timestamp;
            InvolvedActors = involvedActors ?? Array.Empty<string>();
            EmotionalWeight = emotionalWeight;
            Tags = tags ?? Array.Empty<string>();
        }
    }
}
