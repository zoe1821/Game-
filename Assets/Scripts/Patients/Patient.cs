using System;
using System.Collections;
using UnityEngine;
using PsychHospital.Hospital;
using PsychHospital.Staffing;
using PsychHospital.Utils;

namespace PsychHospital.Patients
{
    /// V0.2 patient flow: walk to reception, get registered, walk to an available
    /// psychiatrist or psychologist, get seen, then leave. Real diagnosis-based
    /// routing (choosing which specialist based on symptoms) arrives with the
    /// differential-diagnosis system in V0.4 -- for now the doctor is picked at random
    /// between the two consultation roles. If a required role isn't staffed yet, the
    /// patient wanders near the entrance instead of blocking or faking progress, and
    /// picks the flow back up as soon as the hospital catches up.
    public class Patient : MonoBehaviour
    {
        private static readonly string[] ConsultationRoles = { "psychiatrist", "psychologist" };

        public PatientData Data { get; private set; }
        public event Action<Patient> OnDespawned;

        private HospitalGrid grid;
        private StaffManager staffManager;
        private System.Random rng;
        private GridMover mover;
        private Vector2Int exitCell;

        public void Initialize(PatientData data, HospitalGrid hospitalGrid, StaffManager staff,
            System.Random random, Vector3 spawnWorldPos, Vector2Int exit)
        {
            Data = data;
            grid = hospitalGrid;
            staffManager = staff;
            rng = random;
            exitCell = exit;

            transform.position = spawnWorldPos;
            gameObject.name = $"Patient_{data.fullName.Replace(' ', '_')}";

            Color color = data.sex == PatientSex.Masculino
                ? new Color(0.30f, 0.55f, 0.85f)
                : new Color(0.85f, 0.40f, 0.55f);

            var renderer = gameObject.AddComponent<SpriteRenderer>();
            renderer.sprite = SpriteFactory.CreateCircleSprite(color);
            renderer.sortingOrder = 2;

            mover = gameObject.AddComponent<GridMover>();
            mover.Initialize(grid);

            StartCoroutine(Run());
        }

        private IEnumerator Run()
        {
            yield return VisitRole("receptionist");

            string doctorRole = ConsultationRoles[rng.Next(ConsultationRoles.Length)];
            yield return VisitRole(doctorRole);

            yield return WalkTo(exitCell);
            Destroy(gameObject);
        }

        private IEnumerator VisitRole(string roleId)
        {
            RoomInstance room = staffManager.GetAnyStaffedRoomForRole(roleId);
            while (room == null)
            {
                yield return WalkTo(grid.GetRandomFreeCell(rng));
                room = staffManager.GetAnyStaffedRoomForRole(roleId);
            }

            yield return WalkTo(room.EntrancePoint);

            Staff attendingStaff = staffManager.GetStaffInRoom(room);
            while (attendingStaff.IsBusy)
            {
                yield return new WaitForSeconds(0.5f);
            }

            attendingStaff.IsBusy = true;
            // serviceMinutes is used as real seconds for V0.2 pacing; once treatment/
            // diagnosis exist this should run off TimeManager instead.
            yield return new WaitForSeconds(Mathf.Max(1f, attendingStaff.RoleData.serviceMinutes * 0.5f));
            attendingStaff.IsBusy = false;
        }

        private IEnumerator WalkTo(Vector2Int cell)
        {
            if (!mover.MoveTo(cell))
            {
                yield return null;
                yield break;
            }
            while (mover.IsMoving) yield return null;
        }

        private void OnDestroy()
        {
            OnDespawned?.Invoke(this);
        }
    }
}
