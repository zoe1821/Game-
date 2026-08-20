using System;
using System.Collections.Generic;
using UnityEngine;

namespace PsychHospital.Hospital
{
    /// Shared path-following component used by both patients and staff: given a
    /// destination cell, finds a route around occupied (built) cells and walks it.
    public class GridMover : MonoBehaviour
    {
        public float moveSpeed = 2f;
        public bool IsMoving { get; private set; }

        private HospitalGrid grid;
        private List<Vector2Int> path;
        private int pathIndex;
        private Action onArrived;

        public void Initialize(HospitalGrid hospitalGrid)
        {
            grid = hospitalGrid;
        }

        public bool MoveTo(Vector2Int destinationCell, Action onArrivedCallback = null)
        {
            Vector2Int start = grid.WorldToCell(transform.position);
            List<Vector2Int> newPath = GridPathfinder.FindPath(grid, start, destinationCell);
            if (newPath == null || newPath.Count == 0) return false;

            path = newPath;
            pathIndex = 0;
            onArrived = onArrivedCallback;
            IsMoving = true;
            return true;
        }

        private void Update()
        {
            if (!IsMoving || path == null) return;

            Vector3 targetWorld = grid.CellToWorldCenter(path[pathIndex]);
            transform.position = Vector3.MoveTowards(transform.position, targetWorld, moveSpeed * Time.deltaTime);

            if (Vector3.Distance(transform.position, targetWorld) >= 0.03f) return;

            pathIndex++;
            if (pathIndex < path.Count) return;

            IsMoving = false;
            path = null;
            Action callback = onArrived;
            onArrived = null;
            callback?.Invoke();
        }
    }
}
