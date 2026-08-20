using System.Collections.Generic;
using UnityEngine;

namespace PsychHospital.Hospital
{
    /// Plain breadth-first search over free grid cells. The grid is small (a few
    /// hundred to a couple thousand cells) and paths are only computed when a patient
    /// or staff member picks a new destination, so BFS is cheap enough without needing
    /// a more elaborate A* / navmesh solution yet.
    public static class GridPathfinder
    {
        private static readonly Vector2Int[] Directions =
        {
            Vector2Int.up, Vector2Int.down, Vector2Int.left, Vector2Int.right
        };

        public static List<Vector2Int> FindPath(HospitalGrid grid, Vector2Int start, Vector2Int goal)
        {
            if (start == goal) return new List<Vector2Int> { start };
            if (!grid.InBounds(start) || !grid.InBounds(goal)) return null;

            var frontier = new Queue<Vector2Int>();
            var cameFrom = new Dictionary<Vector2Int, Vector2Int>();
            frontier.Enqueue(start);
            cameFrom[start] = start;

            while (frontier.Count > 0)
            {
                Vector2Int current = frontier.Dequeue();
                if (current == goal) break;

                foreach (Vector2Int dir in Directions)
                {
                    Vector2Int next = current + dir;
                    if (cameFrom.ContainsKey(next)) continue;
                    if (!grid.InBounds(next)) continue;
                    if (!grid.IsWalkable(next) && next != goal) continue;

                    cameFrom[next] = current;
                    frontier.Enqueue(next);
                }
            }

            if (!cameFrom.ContainsKey(goal)) return null;

            var path = new List<Vector2Int>();
            Vector2Int step = goal;
            while (step != start)
            {
                path.Add(step);
                step = cameFrom[step];
            }
            path.Add(start);
            path.Reverse();
            return path;
        }
    }
}
