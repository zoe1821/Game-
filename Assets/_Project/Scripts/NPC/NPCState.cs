using System;
using System.Collections.Generic;
using UnityEngine;

namespace RPG.NPC
{
    public enum EmotionType { Neutral, Happy, Sad, Fear, Anger, Shame, Surprise, Trust, Distrust, Love, Jealousy }

    public enum RelationshipType { Stranger, Acquaintance, Friend, BestFriend, Enemy, Partner, Ex, Family, Coworker, Boss, Teacher }

    /// <summary>Estado en vivo de un NPC: lo unico que persiste/cambia con las acciones del jugador.</summary>
    [Serializable]
    public class NPCState
    {
        public EmotionType CurrentEmotion = EmotionType.Neutral;
        public float EmotionIntensity = 0.2f;

        public RelationshipType RelationshipWithPlayer = RelationshipType.Stranger;
        public float RelationshipScore = 0f; // -100 a 100

        public float Money;
        public string CurrentLocationTag = "";
        public bool IsBusy;

        public List<string> KnownSecretsAboutPlayer = new List<string>();

        public void ApplyRelationshipDelta(float delta)
        {
            RelationshipScore = Mathf.Clamp(RelationshipScore + delta, -100f, 100f);
            RelationshipWithPlayer = ScoreToRelationshipType(RelationshipScore, RelationshipWithPlayer);
        }

        private static RelationshipType ScoreToRelationshipType(float score, RelationshipType current)
        {
            // Las relaciones especiales (Familia, Pareja, Jefe, Profesor...) no se sobrescriben automaticamente
            // por la puntuacion; solo evolucionan las genericas.
            if (current is RelationshipType.Family or RelationshipType.Boss or RelationshipType.Teacher or RelationshipType.Partner or RelationshipType.Ex)
                return current;

            if (score <= -50f) return RelationshipType.Enemy;
            if (score >= 70f) return RelationshipType.BestFriend;
            if (score >= 25f) return RelationshipType.Friend;
            if (score >= 5f) return RelationshipType.Acquaintance;
            return RelationshipType.Stranger;
        }

        public void SetEmotion(EmotionType emotion, float intensity)
        {
            CurrentEmotion = emotion;
            EmotionIntensity = Mathf.Clamp(intensity, 0f, 1f);
        }
    }
}
