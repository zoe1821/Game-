using UnityEngine;
using UnityEngine.EventSystems;

namespace PsychHospital.Hospital
{
    /// Handles build-mode input: player selects a room type from the HUD, then taps a
    /// free cell on the map to place it. Placement is validated against the grid, so
    /// invalid taps are silently rejected rather than faked.
    public class BuildController : MonoBehaviour
    {
        private HospitalManager hospital;
        private Camera worldCamera;
        private string selectedRoomTypeId;

        public bool IsBuilding => !string.IsNullOrEmpty(selectedRoomTypeId);

        public void Initialize(HospitalManager hospitalManager, Camera camera)
        {
            hospital = hospitalManager;
            worldCamera = camera;
        }

        public void SelectRoomType(string roomTypeId)
        {
            selectedRoomTypeId = roomTypeId;
        }

        public void CancelBuild()
        {
            selectedRoomTypeId = null;
        }

        private void Update()
        {
            if (!IsBuilding || IsPointerOverUI()) return;

            Vector3? tapWorldPos = GetTapWorldPosition();
            if (!tapWorldPos.HasValue) return;

            Vector2Int cell = hospital.Grid.WorldToCell(tapWorldPos.Value);
            if (hospital.TryPlaceRoom(selectedRoomTypeId, cell))
            {
                selectedRoomTypeId = null;
            }
        }

        private bool IsPointerOverUI()
        {
            if (EventSystem.current == null) return false;
            if (Input.touchCount > 0) return EventSystem.current.IsPointerOverGameObject(Input.GetTouch(0).fingerId);
            return EventSystem.current.IsPointerOverGameObject();
        }

        private Vector3? GetTapWorldPosition()
        {
            if (Input.touchCount > 0)
            {
                Touch touch = Input.GetTouch(0);
                if (touch.phase == TouchPhase.Began) return worldCamera.ScreenToWorldPoint(touch.position);
                return null;
            }

            if (Input.GetMouseButtonDown(0)) return worldCamera.ScreenToWorldPoint(Input.mousePosition);
            return null;
        }
    }
}
