using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;
using PsychHospital.Core;
using PsychHospital.Hospital;
using PsychHospital.Patients;

namespace PsychHospital.UI
{
    /// Minimal touch-first HUD for V0.1: day/hour + patient count readout, time-speed
    /// controls, and a room-building palette. Built entirely at runtime (no prefabs)
    /// so the project needs no hand-authored scene assets to function.
    public class HudController : MonoBehaviour
    {
        private TimeManager timeManager;
        private BuildController buildController;
        private RoomDatabase roomDb;
        private PatientManager patientManager;

        private Canvas canvas;
        private Text dayHourText;
        private Text patientCountText;

        public void Initialize(TimeManager time, BuildController build, RoomDatabase rooms, PatientManager patients)
        {
            timeManager = time;
            buildController = build;
            roomDb = rooms;
            patientManager = patients;

            BuildCanvas();
            RefreshTimeText();
        }

        private void Update()
        {
            RefreshTimeText();
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
        }

        private void BuildTopBar()
        {
            RectTransform bar = CreateBar(canvas.transform, "TopBar", top: true, height: 100f);

            dayHourText = CreateText(bar, "DayHourText", "Dia 1 - 08:00", 28, TextAnchor.MiddleLeft);
            SetRect(dayHourText.rectTransform, new Vector2(0.02f, 0f), new Vector2(0.35f, 1f));

            patientCountText = CreateText(bar, "PatientCountText", "Pacientes: 0", 24, TextAnchor.MiddleLeft);
            SetRect(patientCountText.rectTransform, new Vector2(0.35f, 0f), new Vector2(0.62f, 1f));

            string[] labels = { "||", "1x", "2x", "3x" };
            int[] speeds = { 0, 1, 2, 3 };
            for (int i = 0; i < labels.Length; i++)
            {
                int speed = speeds[i];
                Button btn = CreateButton(bar, $"Speed_{labels[i]}", labels[i], () => timeManager.SetSpeed(speed));
                float x0 = 0.68f + i * 0.075f;
                SetRect(btn.GetComponent<RectTransform>(), new Vector2(x0, 0.2f), new Vector2(x0 + 0.07f, 0.8f));
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

        private void RefreshTimeText()
        {
            int hour = Mathf.FloorToInt(timeManager.CurrentHour);
            int minute = Mathf.FloorToInt((timeManager.CurrentHour - hour) * 60f);
            dayHourText.text = $"Dia {timeManager.CurrentDay} - {hour:00}:{minute:00}";
            if (patientManager != null) patientCountText.text = $"Pacientes: {patientManager.ActivePatients.Count}";
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
