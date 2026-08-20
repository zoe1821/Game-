using UnityEngine;

namespace PsychHospital.Core
{
    /// Touch pan (1 finger drag) + pinch zoom (2 fingers), with mouse drag/scroll
    /// fallback for testing in the Editor. Camera stays clamped to the hospital plot.
    public class CameraController : MonoBehaviour
    {
        public float minZoom = 3f;
        public float maxZoom = 15f;

        private Camera cam;
        private Bounds bounds;
        private Vector3 mouseDragOrigin;
        private bool mouseDragging;

        public void Initialize(Camera worldCamera, Bounds worldBounds)
        {
            cam = worldCamera;
            bounds = worldBounds;
        }

        private void Update()
        {
            if (cam == null) return;
            HandleZoom();
            HandlePan();
            ClampToBounds();
        }

        private void HandleZoom()
        {
            if (Input.touchCount == 2)
            {
                Touch t0 = Input.GetTouch(0);
                Touch t1 = Input.GetTouch(1);
                Vector2 prev0 = t0.position - t0.deltaPosition;
                Vector2 prev1 = t1.position - t1.deltaPosition;
                float prevDist = (prev0 - prev1).magnitude;
                float curDist = (t0.position - t1.position).magnitude;
                float delta = prevDist - curDist;
                cam.orthographicSize = Mathf.Clamp(cam.orthographicSize + delta * 0.02f, minZoom, maxZoom);
                return;
            }

            float scroll = Input.GetAxis("Mouse ScrollWheel");
            if (Mathf.Abs(scroll) > 0.0001f)
            {
                cam.orthographicSize = Mathf.Clamp(cam.orthographicSize - scroll * 5f, minZoom, maxZoom);
            }
        }

        private void HandlePan()
        {
            if (Input.touchCount == 1)
            {
                Touch touch = Input.GetTouch(0);
                if (touch.phase == TouchPhase.Moved)
                {
                    Vector3 worldNow = cam.ScreenToWorldPoint(new Vector3(touch.position.x, touch.position.y, 0f));
                    Vector3 worldPrev = cam.ScreenToWorldPoint(new Vector3(
                        touch.position.x - touch.deltaPosition.x,
                        touch.position.y - touch.deltaPosition.y, 0f));
                    cam.transform.position -= worldNow - worldPrev;
                }
                return;
            }

            if (Input.GetMouseButtonDown(1) || Input.GetMouseButtonDown(2))
            {
                mouseDragging = true;
                mouseDragOrigin = cam.ScreenToWorldPoint(Input.mousePosition);
            }
            else if (Input.GetMouseButtonUp(1) || Input.GetMouseButtonUp(2))
            {
                mouseDragging = false;
            }

            if (mouseDragging)
            {
                Vector3 current = cam.ScreenToWorldPoint(Input.mousePosition);
                cam.transform.position += mouseDragOrigin - current;
            }
        }

        private void ClampToBounds()
        {
            float halfHeight = cam.orthographicSize;
            float halfWidth = halfHeight * cam.aspect;

            float minX = bounds.min.x + halfWidth;
            float maxX = bounds.max.x - halfWidth;
            float minY = bounds.min.y + halfHeight;
            float maxY = bounds.max.y - halfHeight;

            Vector3 pos = cam.transform.position;
            pos.x = minX <= maxX ? Mathf.Clamp(pos.x, minX, maxX) : bounds.center.x;
            pos.y = minY <= maxY ? Mathf.Clamp(pos.y, minY, maxY) : bounds.center.y;
            cam.transform.position = pos;
        }
    }
}
