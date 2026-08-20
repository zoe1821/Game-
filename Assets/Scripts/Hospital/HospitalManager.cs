using System;
using System.Collections.Generic;
using UnityEngine;
using PsychHospital.Utils;

namespace PsychHospital.Hospital
{
    public class HospitalManager : MonoBehaviour
    {
        public HospitalGrid Grid { get; private set; }
        public RoomDatabase RoomDb { get; private set; }
        public IReadOnlyList<RoomInstance> BuiltRooms => builtRooms;

        /// Fired right after a room finishes construction, so systems that place staff
        /// or route patients can react to newly available rooms without polling.
        public event Action<RoomInstance> OnRoomBuilt;

        private readonly List<RoomInstance> builtRooms = new List<RoomInstance>();
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
            room.SetEntrancePoint(FindEntrancePoint(origin, size));

            builtRooms.Add(room);
            OnRoomBuilt?.Invoke(room);
            return true;
        }

        private Vector2Int FindEntrancePoint(Vector2Int origin, Vector2Int size)
        {
            for (int x = origin.x; x < origin.x + size.x; x++)
            {
                var below = new Vector2Int(x, origin.y - 1);
                if (Grid.IsWalkable(below)) return below;
            }
            for (int x = origin.x; x < origin.x + size.x; x++)
            {
                var above = new Vector2Int(x, origin.y + size.y);
                if (Grid.IsWalkable(above)) return above;
            }
            for (int y = origin.y; y < origin.y + size.y; y++)
            {
                var left = new Vector2Int(origin.x - 1, y);
                if (Grid.IsWalkable(left)) return left;
            }
            for (int y = origin.y; y < origin.y + size.y; y++)
            {
                var right = new Vector2Int(origin.x + size.x, y);
                if (Grid.IsWalkable(right)) return right;
            }
            return origin;
        }
    }
}
