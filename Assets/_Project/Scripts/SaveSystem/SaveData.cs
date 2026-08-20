using System;
using System.Collections.Generic;
using RPG.TimeSystem;

namespace RPG.SaveSystem
{
    [Serializable]
    public class InventoryEntrySave
    {
        public string ItemId;
        public int Quantity;
    }

    [Serializable]
    public class PlayerSaveData
    {
        public float PositionX;
        public float PositionY;
        public float Health;
        public float Energy;
        public float Money;
        public int PowerLevel;
        public float PowerExperience;
        public List<InventoryEntrySave> Inventory = new List<InventoryEntrySave>();
    }

    [Serializable]
    public class MemoryEntrySave
    {
        public string Description;
        public GameDateTime Timestamp;
        public string[] InvolvedActors;
        public float EmotionalWeight;
        public string[] Tags;
    }

    [Serializable]
    public class NpcSaveData
    {
        public string NpcId;
        public float PositionX;
        public float PositionY;
        public string RelationshipType;
        public float RelationshipScore;
        public string CurrentEmotion;
        public float EmotionIntensity;
        public float Money;
        public List<MemoryEntrySave> Memories = new List<MemoryEntrySave>();
    }

    [Serializable]
    public class WorldObjectSaveData
    {
        public string ObjectId;
        public float PositionX;
        public float PositionY;
        public string State;
        public string OwnerId;
    }

    [Serializable]
    public class SaveGameData
    {
        public GameDateTime Time;
        public PlayerSaveData Player = new PlayerSaveData();
        public List<NpcSaveData> Npcs = new List<NpcSaveData>();
        public List<WorldObjectSaveData> WorldObjects = new List<WorldObjectSaveData>();
    }
}
