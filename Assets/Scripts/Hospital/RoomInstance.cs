using UnityEngine;
using PsychHospital.Utils;

namespace PsychHospital.Hospital
{
    public class RoomInstance : MonoBehaviour
    {
        public RoomTypeData RoomType { get; private set; }
        public Vector2Int Origin { get; private set; }
        public Vector2Int Size { get; private set; }

        public void Initialize(RoomTypeData roomType, Vector2Int origin, Vector2Int size, HospitalGrid grid)
        {
            RoomType = roomType;
            Origin = origin;
            Size = size;

            transform.position = grid.AreaCenterWorld(origin, size);
            gameObject.name = $"Room_{roomType.id}_{origin.x}_{origin.y}";

            if (!ColorUtility.TryParseHtmlString(roomType.colorHex, out Color color))
            {
                color = Color.gray;
            }

            var renderer = gameObject.AddComponent<SpriteRenderer>();
            renderer.sprite = SpriteFactory.CreateSolidSprite(size.x, size.y, color);
            renderer.sortingOrder = 1;
        }
    }
}
