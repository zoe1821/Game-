using System.Collections.Generic;

namespace PsychHospital.Staffing
{
    public class StaffRoleDatabase
    {
        private readonly Dictionary<string, StaffRoleData> byId = new Dictionary<string, StaffRoleData>();

        public IReadOnlyList<StaffRoleData> All { get; private set; } = new List<StaffRoleData>();

        public void Load(StaffRoleListWrapper data)
        {
            All = data?.roles ?? new List<StaffRoleData>();
            byId.Clear();
            foreach (var role in All)
            {
                byId[role.id] = role;
            }
        }

        public bool TryGet(string id, out StaffRoleData role) => byId.TryGetValue(id, out role);
    }
}
