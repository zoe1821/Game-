using UnityEngine;

namespace PsychHospital.Hospital
{
    public class GridCell
    {
        public bool isFree = true;
        public RoomInstance room;
    }

    /// Authoritative buildable grid for the hospital plot. World units map 1:1 to cells
    /// (cellSize = 1) so world<->cell conversion stays trivial.
    public class HospitalGrid
    {
        public readonly int width;
        public readonly int height;
        public const float CellSize = 1f;

        private readonly GridCell[,] cells;

        public HospitalGrid(int width, int height)
        {
            this.width = width;
            this.height = height;
            cells = new GridCell[width, height];
            for (int x = 0; x < width; x++)
            {
                for (int y = 0; y < height; y++)
                {
                    cells[x, y] = new GridCell();
                }
            }
        }

        public bool InBounds(Vector2Int cell) =>
            cell.x >= 0 && cell.y >= 0 && cell.x < width && cell.y < height;

        public bool IsAreaFree(Vector2Int origin, Vector2Int size)
        {
            for (int x = origin.x; x < origin.x + size.x; x++)
            {
                for (int y = origin.y; y < origin.y + size.y; y++)
                {
                    var cell = new Vector2Int(x, y);
                    if (!InBounds(cell) || !cells[x, y].isFree) return false;
                }
            }
            return true;
        }

        public void OccupyArea(Vector2Int origin, Vector2Int size, RoomInstance room)
        {
            for (int x = origin.x; x < origin.x + size.x; x++)
            {
                for (int y = origin.y; y < origin.y + size.y; y++)
                {
                    cells[x, y].isFree = false;
                    cells[x, y].room = room;
                }
            }
        }

        public Vector2Int WorldToCell(Vector3 world) =>
            new Vector2Int(Mathf.FloorToInt(world.x / CellSize), Mathf.FloorToInt(world.y / CellSize));

        public Vector3 CellToWorldCenter(Vector2Int cell) =>
            new Vector3((cell.x + 0.5f) * CellSize, (cell.y + 0.5f) * CellSize, 0f);

        public Vector3 AreaCenterWorld(Vector2Int origin, Vector2Int size) =>
            new Vector3((origin.x + size.x / 2f) * CellSize, (origin.y + size.y / 2f) * CellSize, 0f);

        public Bounds WorldBounds => new Bounds(
            new Vector3(width * CellSize / 2f, height * CellSize / 2f, 0f),
            new Vector3(width * CellSize, height * CellSize, 0f));

        public Vector2Int GetRandomFreeCell(System.Random rng)
        {
            for (int attempt = 0; attempt < 50; attempt++)
            {
                var candidate = new Vector2Int(rng.Next(0, width), rng.Next(0, height));
                if (cells[candidate.x, candidate.y].isFree) return candidate;
            }
            return new Vector2Int(width / 2, height / 2);
        }
    }
}
