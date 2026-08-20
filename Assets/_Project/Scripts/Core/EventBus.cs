using System;
using UnityEngine;

namespace RPG.Core
{
    /// <summary>
    /// Canal de eventos global y desacoplado. Los sistemas se comunican publicando/escuchando
    /// aqui en lugar de mantener referencias directas entre si. Esto permite anadir sistemas
    /// nuevos (Fase 2+) sin modificar los existentes.
    /// </summary>
    public static class EventBus
    {
        public static event Action<int> OnHourChanged;
        public static event Action<int> OnDayChanged;

        public static event Action<string, string> OnRelationshipChanged; // (npcId, relationshipType)
        public static event Action<string, string> OnMemoryRecorded;      // (npcId, description)

        /// <summary>Algo perceptible ocurrio en el mundo (golpe, rotura, grito...). Los NPC cercanos deciden si lo recuerdan.</summary>
        public static event Action<WorldEvent> OnWorldEvent;

        public static event Action<string> OnJournalEntry; // texto narrativo para el diario del jugador

        public static void RaiseHourChanged(int hour) => OnHourChanged?.Invoke(hour);
        public static void RaiseDayChanged(int day) => OnDayChanged?.Invoke(day);
        public static void RaiseRelationshipChanged(string npcId, string relationshipType) => OnRelationshipChanged?.Invoke(npcId, relationshipType);
        public static void RaiseMemoryRecorded(string npcId, string description) => OnMemoryRecorded?.Invoke(npcId, description);
        public static void RaiseWorldEvent(WorldEvent worldEvent) => OnWorldEvent?.Invoke(worldEvent);
        public static void RaiseJournalEntry(string text) => OnJournalEntry?.Invoke(text);
    }

    /// <summary>Descripcion de un suceso que los NPC cercanos podrian percibir y memorizar.</summary>
    public readonly struct WorldEvent
    {
        public readonly string Description;
        public readonly Vector2 Position;
        public readonly float Radius;
        public readonly string ActorId;

        public WorldEvent(string description, Vector2 position, float radius, string actorId)
        {
            Description = description;
            Position = position;
            Radius = radius;
            ActorId = actorId;
        }
    }
}
