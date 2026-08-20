using UnityEngine;
using PsychHospital.Hospital;
using PsychHospital.Utils;

namespace PsychHospital.Staffing
{
    /// Visual/behavioral representation of a hired staff member. Once hired they walk
    /// to their assigned room and stay there serving patients; shifts/commuting are not
    /// part of V0.2.
    public class Staff : MonoBehaviour
    {
        public StaffData Data { get; private set; }
        public StaffRoleData RoleData { get; private set; }
        public RoomInstance AssignedRoom { get; private set; }
        public bool IsBusy { get; set; }

        private GridMover mover;

        public void Initialize(StaffData data, StaffRoleData roleData, HospitalGrid grid, Vector3 spawnWorldPos)
        {
            Data = data;
            RoleData = roleData;
            transform.position = spawnWorldPos;
            gameObject.name = $"Staff_{roleData.id}_{data.fullName.Replace(' ', '_')}";

            Color color = ColorUtility.TryParseHtmlString(roleData.colorHex, out Color parsed) ? parsed : Color.white;
            var renderer = gameObject.AddComponent<SpriteRenderer>();
            renderer.sprite = SpriteFactory.CreateSolidSprite(1, 1, color, pixelsPerCell: 24);
            renderer.sortingOrder = 2;

            mover = gameObject.AddComponent<GridMover>();
            mover.Initialize(grid);
        }

        public void AssignToRoom(RoomInstance room)
        {
            AssignedRoom = room;
            mover.MoveTo(room.EntrancePoint);
        }
    }
}
