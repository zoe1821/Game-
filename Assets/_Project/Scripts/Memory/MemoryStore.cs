using System.Collections.Generic;
using System.Linq;

namespace RPG.Memory
{
    /// <summary>
    /// Contenedor de recuerdos persistentes de un NPC. No se olvida nada automaticamente:
    /// los recuerdos solo se atenuan en influencia mediante EmotionalWeight al calcular relaciones,
    /// nunca se borran salvo limite de capacidad por rendimiento.
    /// </summary>
    public class MemoryStore
    {
        private const int MaxEntries = 500;

        private readonly List<MemoryEntry> _entries = new List<MemoryEntry>();

        public IReadOnlyList<MemoryEntry> Entries => _entries;

        public void Add(MemoryEntry entry)
        {
            _entries.Add(entry);
            if (_entries.Count > MaxEntries)
                _entries.RemoveAt(0); // descarta el recuerdo mas antiguo solo por limite tecnico
        }

        public IEnumerable<MemoryEntry> GetAbout(string actorId) =>
            _entries.Where(e => e.InvolvedActors.Contains(actorId));

        public IEnumerable<MemoryEntry> GetByTag(string tag) =>
            _entries.Where(e => e.Tags.Contains(tag));

        public IEnumerable<MemoryEntry> GetRecent(int count) =>
            _entries.Skip(System.Math.Max(0, _entries.Count - count));

        public float GetTotalEmotionalWeightAbout(string actorId) =>
            GetAbout(actorId).Sum(e => e.EmotionalWeight);

        public void LoadEntries(IEnumerable<MemoryEntry> entries)
        {
            _entries.Clear();
            _entries.AddRange(entries);
        }
    }
}
