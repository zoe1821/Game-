using UnityEngine;
using PsychHospital.Hospital;
using PsychHospital.Utils;

namespace PsychHospital.Patients
{
    /// Visual/behavioral representation of a patient on the map. For V0.1 this is
    /// deliberately simple: a colored marker that wanders between free floor cells.
    /// Real navigation (avoiding rooms/staff, walking to assigned destinations) is
    /// scoped for V0.2 ("Movimiento de pacientes") per the roadmap.
    public class Patient : MonoBehaviour
    {
        public PatientData Data { get; private set; }

        private HospitalGrid grid;
        private System.Random rng;
        private Vector3 targetWorldPos;
        private float waitTimer;
        private const float MoveSpeed = 1.5f;

        public void Initialize(PatientData data, HospitalGrid hospitalGrid, System.Random random, Vector3 spawnWorldPos)
        {
            Data = data;
            grid = hospitalGrid;
            rng = random;
            transform.position = spawnWorldPos;
            targetWorldPos = spawnWorldPos;
            gameObject.name = $"Patient_{data.fullName.Replace(' ', '_')}";

            Color color = data.sex == PatientSex.Masculino
                ? new Color(0.30f, 0.55f, 0.85f)
                : new Color(0.85f, 0.40f, 0.55f);

            var renderer = gameObject.AddComponent<SpriteRenderer>();
            renderer.sprite = SpriteFactory.CreateCircleSprite(color);
            renderer.sortingOrder = 2;

            PickNewTarget();
        }

        private void Update()
        {
            transform.position = Vector3.MoveTowards(transform.position, targetWorldPos, MoveSpeed * Time.deltaTime);

            if (Vector3.Distance(transform.position, targetWorldPos) < 0.05f)
            {
                waitTimer -= Time.deltaTime;
                if (waitTimer <= 0f) PickNewTarget();
            }
        }

        private void PickNewTarget()
        {
            Vector2Int cell = grid.GetRandomFreeCell(rng);
            targetWorldPos = grid.CellToWorldCenter(cell);
            waitTimer = (float)(rng.NextDouble() * 5.0 + 2.0);
        }
    }
}
