using System.Collections.Generic;
using UnityEngine;
using PsychHospital.Hospital;
using PsychHospital.Patients;

namespace PsychHospital.Staffing
{
    /// Handles hiring and room assignment (design doc section 4 / bucle principal step
    /// 2 "Contratar personal"). A hired staff member is assigned to the first built,
    /// unstaffed room matching their role; if none exists yet they wait until
    /// HospitalManager reports a matching room being built.
    public class StaffManager : MonoBehaviour
    {
        private HospitalGrid grid;
        private StaffRoleDatabase roleDb;
        private HospitalManager hospitalManager;
        private PatientNameData names;

        private readonly List<Staff> allStaff = new List<Staff>();
        private readonly List<Staff> unassignedStaff = new List<Staff>();
        private readonly HashSet<RoomInstance> staffedRooms = new HashSet<RoomInstance>();
        private readonly System.Random rng = new System.Random();
        private int nextId = 1;

        public IReadOnlyList<Staff> AllStaff => allStaff;

        public void Initialize(HospitalGrid hospitalGrid, StaffRoleDatabase roles, HospitalManager hospital, PatientNameData nameData)
        {
            grid = hospitalGrid;
            roleDb = roles;
            hospitalManager = hospital;
            names = nameData;
            hospitalManager.OnRoomBuilt += HandleRoomBuilt;
        }

        private void OnDestroy()
        {
            if (hospitalManager != null) hospitalManager.OnRoomBuilt -= HandleRoomBuilt;
        }

        public bool HireStaff(string roleId)
        {
            if (!roleDb.TryGet(roleId, out StaffRoleData roleData)) return false;
            if (names == null || names.lastNames == null || names.lastNames.Count == 0) return false;

            var data = new StaffData { id = nextId++, fullName = GenerateName(), role = roleId };
            var go = new GameObject();
            go.transform.SetParent(transform);
            var staff = go.AddComponent<Staff>();
            Vector3 spawn = grid.CellToWorldCenter(new Vector2Int(0, 0));
            staff.Initialize(data, roleData, grid, spawn);
            allStaff.Add(staff);

            RoomInstance room = FindUnstaffedRoom(roleData.roomId);
            if (room != null)
            {
                AssignStaffToRoom(staff, room);
            }
            else
            {
                unassignedStaff.Add(staff);
            }
            return true;
        }

        /// Prefers an idle staffed room so a second (or third) hire of the same role
        /// actually gets used; only falls back to a busy one -- to queue at -- when
        /// every matching room is occupied.
        public RoomInstance GetAnyStaffedRoomForRole(string roleId)
        {
            RoomInstance busyFallback = null;
            foreach (Staff staff in allStaff)
            {
                if (staff.RoleData.id != roleId || staff.AssignedRoom == null) continue;
                if (!staff.IsBusy) return staff.AssignedRoom;
                if (busyFallback == null) busyFallback = staff.AssignedRoom;
            }
            return busyFallback;
        }

        public Staff GetStaffInRoom(RoomInstance room)
        {
            foreach (Staff staff in allStaff)
            {
                if (staff.AssignedRoom == room) return staff;
            }
            return null;
        }

        private void HandleRoomBuilt(RoomInstance room)
        {
            for (int i = unassignedStaff.Count - 1; i >= 0; i--)
            {
                Staff staff = unassignedStaff[i];
                if (staff.RoleData.roomId != room.RoomType.id) continue;

                unassignedStaff.RemoveAt(i);
                AssignStaffToRoom(staff, room);
                break;
            }
        }

        private void AssignStaffToRoom(Staff staff, RoomInstance room)
        {
            staffedRooms.Add(room);
            staff.AssignToRoom(room);
        }

        private RoomInstance FindUnstaffedRoom(string roomTypeId)
        {
            foreach (RoomInstance room in hospitalManager.BuiltRooms)
            {
                if (room.RoomType.id == roomTypeId && !staffedRooms.Contains(room)) return room;
            }
            return null;
        }

        private string GenerateName()
        {
            bool isMale = rng.NextDouble() < 0.5;
            List<string> pool = isMale ? names.maleFirstNames : names.femaleFirstNames;
            string first = pool[rng.Next(pool.Count)];
            string last = names.lastNames[rng.Next(names.lastNames.Count)];
            return $"{first} {last}";
        }
    }
}
