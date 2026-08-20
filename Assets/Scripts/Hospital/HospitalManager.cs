using UnityEngine;
using PsychHospital.Utils;

namespace PsychHospital.Hospital
{
    public class HospitalManager : MonoBehaviour
    {
        public HospitalGrid Grid { get; private set; }
        public RoomDatabase RoomDb { get; private set; }

        private Transform roomsParent;

        public void Initialize(int width, int height, RoomDatabase roomDatabase)
        {
            Grid = new HospitalGrid(width, height);
            RoomDb = roomDatabase;

            var floorGO = new GameObject("Floor");
            floorGO.transform.SetParent(transform);
            floorGO.transform.position = Vector3.zero;
            var floorRenderer = floorGO.AddComponent<SpriteRenderer>();
            floorRenderer.sprite = SpriteFactory.CreateFloorSprite(width, height);
            floorRenderer.sortingOrder = 0;

            var roomsGO = new GameObject("Rooms");
            roomsGO.transform.SetParent(transform);
            roomsParent = roomsGO.transform;
        }

        public bool TryPlaceRoom(string roomTypeId, Vector2Int origin)
        {
            if (!RoomDb.TryGet(roomTypeId, out RoomTypeData type)) return false;

            var size = new Vector2Int(type.width, type.height);
            if (!Grid.IsAreaFree(origin, size)) return false;

            var go = new GameObject();
            go.transform.SetParent(roomsParent);
            var room = go.AddComponent<RoomInstance>();
            room.Initialize(type, origin, size, Grid);
            Grid.OccupyArea(origin, size, room);
            return true;
        }
    }
}
