using System;
using System.Collections.Generic;

namespace PsychHospital.Staffing
{
    /// V0.2 staff record. Deeper per-role attributes from design doc section 4
    /// (diagnostico, farmacologia, empatia, estres, etc.) belong to the versions that
    /// actually consume them (diagnosis in V0.4, treatment in V0.5) -- adding them here
    /// now would just be inert fields nothing reads yet.
    [Serializable]
    public class StaffData
    {
        public int id;
        public string fullName;
        public string role;
    }

    /// Data-driven definition of a hireable role: which room it staffs and how long its
    /// service takes. Matches the RoomTypeData pattern used for rooms.json.
    [Serializable]
    public class StaffRoleData
    {
        public string id;
        public string displayName;
        public string roomId;
        public string colorHex;
        public int serviceMinutes;
    }

    [Serializable]
    public class StaffRoleListWrapper
    {
        public List<StaffRoleData> roles;
    }
}
