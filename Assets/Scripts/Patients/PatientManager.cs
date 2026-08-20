using System.Collections.Generic;
using UnityEngine;
using PsychHospital.Core;
using PsychHospital.Hospital;

namespace PsychHospital.Patients
{
    /// Spawns procedurally generated patients over in-game time (design doc section 5).
    /// Arrival cadence is driven by TimeManager, not real seconds, so it scales with
    /// game speed and pausing like everything else in the simulation.
    public class PatientManager : MonoBehaviour
    {
        private const float SpawnIntervalHours = 3f;
        private const int MaxPatients = 10;

        private HospitalGrid grid;
        private PatientNameData names;
        private TimeManager timeManager;
        private readonly System.Random rng = new System.Random();
        private readonly List<Patient> activePatients = new List<Patient>();

        private int nextId = 1000;
        private float hoursSinceLastSpawn;
        private float lastKnownHour;

        public IReadOnlyList<Patient> ActivePatients => activePatients;

        public void Initialize(HospitalGrid hospitalGrid, PatientNameData nameData, TimeManager time)
        {
            grid = hospitalGrid;
            names = nameData;
            timeManager = time;
            lastKnownHour = timeManager.CurrentHour;
            timeManager.OnHourChanged += HandleHourChanged;

            SpawnPatient();
        }

        private void OnDestroy()
        {
            if (timeManager != null) timeManager.OnHourChanged -= HandleHourChanged;
        }

        private void HandleHourChanged(float hour)
        {
            float delta = hour - lastKnownHour;
            if (delta < 0) delta += 24f;
            lastKnownHour = hour;

            hoursSinceLastSpawn += delta;
            if (hoursSinceLastSpawn < SpawnIntervalHours || activePatients.Count >= MaxPatients) return;

            hoursSinceLastSpawn = 0f;
            SpawnPatient();
        }

        private void SpawnPatient()
        {
            if (names == null || names.lastNames == null || names.lastNames.Count == 0) return;

            PatientData data = GeneratePatientData();
            var go = new GameObject();
            go.transform.SetParent(transform);
            var patient = go.AddComponent<Patient>();
            Vector3 spawnPos = grid.CellToWorldCenter(new Vector2Int(0, 0));
            patient.Initialize(data, grid, rng, spawnPos);
            activePatients.Add(patient);
        }

        private PatientData GeneratePatientData()
        {
            bool isMale = rng.NextDouble() < 0.5;
            List<string> firstPool = isMale ? names.maleFirstNames : names.femaleFirstNames;
            string first = firstPool[rng.Next(firstPool.Count)];
            string last = names.lastNames[rng.Next(names.lastNames.Count)];

            return new PatientData
            {
                id = nextId++,
                fullName = $"{first} {last}",
                age = rng.Next(18, 76),
                sex = isMale ? PatientSex.Masculino : PatientSex.Femenino
            };
        }
    }
}
