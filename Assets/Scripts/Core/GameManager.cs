using System.Collections;
using UnityEngine;
using PsychHospital.Data;
using PsychHospital.Hospital;
using PsychHospital.Patients;
using PsychHospital.Staffing;
using PsychHospital.UI;

namespace PsychHospital.Core
{
    /// Entry point. Loads data-driven content (rooms, staff roles, patient names) from
    /// StreamingAssets, then wires up the grid, camera, build system, staffing, patient
    /// spawner and HUD. Everything below GameManager is created at runtime so the
    /// project has no hand-authored scene assets to keep in sync with the code.
    public class GameManager : MonoBehaviour
    {
        public static GameManager Instance { get; private set; }

        [SerializeField] private int gridWidth = 40;
        [SerializeField] private int gridHeight = 24;

        private TimeManager timeManager;
        private HospitalManager hospitalManager;
        private StaffManager staffManager;
        private PatientManager patientManager;
        private CameraController cameraController;
        private BuildController buildController;
        private HudController hudController;

        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }
            Instance = this;
            Screen.orientation = ScreenOrientation.LandscapeLeft;
        }

        private void Start()
        {
            StartCoroutine(InitializeGame());
        }

        private IEnumerator InitializeGame()
        {
            RoomTypeListWrapper roomData = null;
            yield return JsonDataService.LoadStreamingAsset<RoomTypeListWrapper>("Data/rooms.json", r => roomData = r);

            StaffRoleListWrapper staffRoleData = null;
            yield return JsonDataService.LoadStreamingAsset<StaffRoleListWrapper>("Data/staff.json", s => staffRoleData = s);

            PatientNameData nameData = null;
            yield return JsonDataService.LoadStreamingAsset<PatientNameData>("Data/patient_names.json", n => nameData = n);

            var roomDb = new RoomDatabase();
            roomDb.Load(roomData);

            var staffRoleDb = new StaffRoleDatabase();
            staffRoleDb.Load(staffRoleData);

            timeManager = gameObject.AddComponent<TimeManager>();

            hospitalManager = gameObject.AddComponent<HospitalManager>();
            hospitalManager.Initialize(gridWidth, gridHeight, roomDb);

            Camera cam = CreateMainCamera();

            cameraController = gameObject.AddComponent<CameraController>();
            cameraController.Initialize(cam, hospitalManager.Grid.WorldBounds);

            buildController = gameObject.AddComponent<BuildController>();
            buildController.Initialize(hospitalManager, cam);

            staffManager = gameObject.AddComponent<StaffManager>();
            staffManager.Initialize(hospitalManager.Grid, staffRoleDb, hospitalManager, nameData);

            patientManager = gameObject.AddComponent<PatientManager>();
            patientManager.Initialize(hospitalManager.Grid, nameData, timeManager, staffManager);

            hudController = gameObject.AddComponent<HudController>();
            hudController.Initialize(timeManager, buildController, roomDb, patientManager, staffManager, staffRoleDb);

            timeManager.SetSpeed(1);
        }

        private Camera CreateMainCamera()
        {
            var camGO = new GameObject("Main Camera");
            camGO.tag = "MainCamera";

            var cam = camGO.AddComponent<Camera>();
            cam.orthographic = true;
            cam.orthographicSize = 8f;
            cam.backgroundColor = new Color(0.05f, 0.05f, 0.08f);
            cam.clearFlags = CameraClearFlags.SolidColor;

            Bounds bounds = hospitalManager.Grid.WorldBounds;
            camGO.transform.position = new Vector3(bounds.center.x, bounds.center.y, -10f);

            return cam;
        }
    }
}
