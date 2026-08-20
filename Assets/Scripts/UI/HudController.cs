using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;
using PsychHospital.Core;
using PsychHospital.Hospital;
using PsychHospital.Patients;
using PsychHospital.Staffing;

namespace PsychHospital.UI
{
    /// Touch-first HUD: day/hour + patient/staff counters, time-speed controls, a
    /// room-building palette and a staff-hiring panel. Built entirely at runtime (no
    /// prefabs) so the project needs no hand-authored scene assets to function.
    public class HudController : MonoBehaviour
    {
        private TimeManager timeManager;
        private BuildController buildController;
        private RoomDatabase roomDb;
        private PatientManager patientManager;
        private StaffManager staffManager;
        private StaffRoleDatabase staffRoleDb;

        private Canvas canvas;
        private Text dayHourText;
        private Text patientCountText;
        private Text staffCountText;

        public void Initialize(TimeManager time, BuildController build, RoomDatabase rooms,
            PatientManager patients, StaffManager staff, StaffRoleDatabase staffRoles)
        {
            timeManager = time;
            buildController = build;
            roomDb = rooms;
            patientManager = patients;
            staffManager = staff;
            staffRoleDb = staffRoles;

            BuildCanvas();
            RefreshCounters();
        }

        private void Update()
        {
            RefreshCounters();
        }

        private void BuildCanvas()
        {
            var canvasGO = new GameObject("HUD_Canvas");
            canvasGO.transform.SetParent(transform);
            canvas = canvasGO.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;

            var scaler = canvasGO.AddComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1280, 720);
            scaler.matchWidthOrHeight = 0.5f;

            canvasGO.AddComponent<GraphicRaycaster>();

            if (EventSystem.current == null)
            {
                var esGO = new GameObject("EventSystem");
                esGO.AddComponent<EventSystem>();
                esGO.AddComponent<StandaloneInputModule>();
            }

            BuildTopBar();
            BuildBottomBar();
            BuildStaffPanel();
        }

        private void BuildTopBar()
        {
            RectTransform bar = CreateBar(canvas.transform, "TopBar", top: true, height: 100f);

            dayHourText = CreateText(bar, "DayHourText", "Dia 1 - 08:00", 26, TextAnchor.MiddleLeft);
            SetRect(dayHourText.rectTransform, new Vector2(0.02f, 0f), new Vector2(0.28f, 1f));

            patientCountText = CreateText(bar, "PatientCountText", "Pacientes: 0", 22, TextAnchor.MiddleLeft);
            SetRect(patientCountText.rectTransform, new Vector2(0.28f, 0f), new Vector2(0.5f, 1f));

            staffCountText = CreateText(bar, "StaffCountText", "Personal: 0", 22, TextAnchor.MiddleLeft);
            SetRect(staffCountText.rectTransform, new Vector2(0.5f, 0f), new Vector2(0.68f, 1f));

            string[] labels = { "||", "1x", "2x", "3x" };
            int[] speeds = { 0, 1, 2, 3 };
            for (int i = 0; i < labels.Length; i++)
            {
                int speed = speeds[i];
                Button btn = CreateButton(bar, $"Speed_{labels[i]}", labels[i], () => timeManager.SetSpeed(speed));
                float x0 = 0.70f + i * 0.07f;
                SetRect(btn.GetComponent<RectTransform>(), new Vector2(x0, 0.2f), new Vector2(x0 + 0.065f, 0.8f));
            }
        }

        private void BuildBottomBar()
        {
            RectTransform bar = CreateBar(canvas.transform, "BottomBar", top: false, height: 130f);

            var rooms = roomDb.All;
            int count = Mathf.Max(rooms.Count, 1);
            float slot = 1f / count;
            for (int i = 0; i < rooms.Count; i++)
            {
                RoomTypeData room = rooms[i];
                Button btn = CreateButton(bar, $"Build_{room.id}", room.displayName, () => buildController.SelectRoomType(room.id));
                SetRect(btn.GetComponent<RectTransform>(), new Vector2(i * slot + 0.004f, 0.1f), new Vector2((i + 1) * slot - 0.004f, 0.9f));
            }

            Button cancelBtn = CreateButton(canvas.transform, "CancelBuild", "X", () => buildController.CancelBuild());
            SetRect(cancelBtn.GetComponent<RectTransform>(), new Vector2(0.94f, 0.85f), new Vector2(0.99f, 0.95f));
        }

        private void BuildStaffPanel()
        {
            RectTransform panel = CreateSidePanel(canvas.transform, "StaffPanel", 170f);

            var roles = staffRoleDb.All;
            int count = Mathf.Max(roles.Count, 1);
            float slot = 1f / count;
            for (int i = 0; i < roles.Count; i++)
            {
                StaffRoleData role = roles[i];
                Button btn = CreateButton(panel, $"Hire_{role.id}", $"Contratar\n{role.displayName}", () => staffManager.HireStaff(role.id));
                SetRect(btn.GetComponent<RectTransform>(), new Vector2(0.08f, i * slot + 0.05f), new Vector2(0.92f, (i + 1) * slot - 0.05f));
            }
        }

        private void RefreshCounters()
        {
            int hour = Mathf.FloorToInt(timeManager.CurrentHour);
            int minute = Mathf.FloorToInt((timeManager.CurrentHour - hour) * 60f);
            dayHourText.text = $"Dia {timeManager.CurrentDay} - {hour:00}:{minute:00}";
            if (patientManager != null) patientCountText.text = $"Pacientes: {patientManager.ActivePatients.Count}";
            if (staffManager != null) staffCountText.text = $"Personal: {staffManager.AllStaff.Count}";
        }

        private static RectTransform CreateBar(Transform parent, string name, bool top, float height)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            var rt = go.AddComponent<RectTransform>();
            rt.anchorMin = new Vector2(0, top ? 1 : 0);
            rt.anchorMax = new Vector2(1, top ? 1 : 0);
            rt.pivot = new Vector2(0.5f, top ? 1 : 0);
            rt.anchoredPosition = Vector2.zero;
            rt.sizeDelta = new Vector2(0, height);
            go.AddComponent<Image>().color = new Color(0.1f, 0.1f, 0.15f, 0.85f);
            return rt;
        }

        private static RectTransform CreateSidePanel(Transform parent, string name, float width)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            var rt = go.AddComponent<RectTransform>();
            rt.anchorMin = new Vector2(0, 0);
            rt.anchorMax = new Vector2(0, 1);
            rt.pivot = new Vector2(0, 0.5f);
            rt.anchoredPosition = Vector2.zero;
            rt.sizeDelta = new Vector2(width, -230f);
            var img = go.AddComponent<Image>();
            img.color = new Color(0.1f, 0.1f, 0.15f, 0.7f);
            return rt;
        }

        private static void SetRect(RectTransform rt, Vector2 anchorMin, Vector2 anchorMax)
        {
            rt.anchorMin = anchorMin;
            rt.anchorMax = anchorMax;
            rt.offsetMin = Vector2.zero;
            rt.offsetMax = Vector2.zero;
        }

        private static Text CreateText(Transform parent, string name, string content, int fontSize, TextAnchor anchor)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.AddComponent<RectTransform>();
            var text = go.AddComponent<Text>();
            text.font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            text.fontSize = fontSize;
            text.alignment = anchor;
            text.color = Color.white;
            text.text = content;
            return text;
        }

        private static Button CreateButton(Transform parent, string name, string label, UnityEngine.Events.UnityAction onClick)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.AddComponent<RectTransform>();
            var image = go.AddComponent<Image>();
            image.color = new Color(0.25f, 0.45f, 0.7f);
            var button = go.AddComponent<Button>();
            button.onClick.AddListener(onClick);

            Text text = CreateText(go.transform, "Label", label, 20, TextAnchor.MiddleCenter);
            SetRect(text.rectTransform, Vector2.zero, Vector2.one);

            return button;
        }
    }
}
