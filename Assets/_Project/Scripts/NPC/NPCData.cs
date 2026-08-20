using UnityEngine;

namespace RPG.NPC
{
    /// <summary>
    /// Plantilla de datos base de un NPC (lo que no cambia con el juego: personalidad,
    /// trasfondo). El estado que si cambia en vivo (emociones, relacion, dinero...) vive en NPCState.
    /// </summary>
    [CreateAssetMenu(fileName = "NewNPC", menuName = "RPG/NPC/NPC Data")]
    public class NPCData : ScriptableObject
    {
        public string npcId;
        public string npcName = "NPC";
        public int age = 20;
        public string profession = "Estudiante";
        public float startingMoney = 20f;
        public Color portraitColor = Color.gray;

        [Header("Personalidad (0 a 1)")]
        [Range(0, 1)] public float friendliness = 0.5f;
        [Range(0, 1)] public float honesty = 0.5f;
        [Range(0, 1)] public float bravery = 0.5f;
        [Range(0, 1)] public float temper = 0.5f;
        [Range(0, 1)] public float intelligence = 0.5f;

        [Header("Trasfondo")]
        public string[] interests;
        public string[] fears;
        public string[] goals;
        [TextArea] public string[] secrets;
    }
}
