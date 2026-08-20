using System.Collections.Generic;

namespace PsychHospital.Hospital
{
    public class RoomDatabase
    {
        private readonly Dictionary<string, RoomTypeData> byId = new Dictionary<string, RoomTypeData>();

        public IReadOnlyList<RoomTypeData> All { get; private set; } = new List<RoomTypeData>();

        public void Load(RoomTypeListWrapper data)
        {
            All = data?.rooms ?? new List<RoomTypeData>();
            byId.Clear();
            foreach (var room in All)
            {
                byId[room.id] = room;
            }
        }

        public bool TryGet(string id, out RoomTypeData type) => byId.TryGetValue(id, out type);
    }
}
