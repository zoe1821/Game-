using System.IO;
using System.Linq;
using UnityEngine;
using RPG.Inventory;
using RPG.NPC;
using RPG.Player;
using RPG.TimeSystem;
using RPG.World;

namespace RPG.SaveSystem
{
    /// <summary>
    /// Guarda y carga el estado completo del mundo en JSON (Application.persistentDataPath).
    /// Es el unico sistema que lee/escribe el archivo de partida.
    /// </summary>
    public class SaveManager
    {
        private const string SaveFileName = "savegame.json";
        private string SavePath => Path.Combine(Application.persistentDataPath, SaveFileName);

        public bool HasSaveFile => File.Exists(SavePath);

        public void Save(TimeManager time, PlayerController playerController, PlayerStats playerStats,
            InventorySystem playerInventory, NPCController[] npcs, WorldObject[] worldObjects)
        {
            var data = new SaveGameData { Time = time.Current };

            data.Player.PositionX = playerController.transform.position.x;
            data.Player.PositionY = playerController.transform.position.y;
            data.Player.Health = playerStats.Health;
            data.Player.Energy = playerStats.Energy;
            data.Player.Money = playerStats.Money;
            data.Player.PowerLevel = playerStats.PowerLevel;

            foreach (var entry in playerInventory.Entries)
            {
                data.Player.Inventory.Add(new InventoryEntrySave { ItemId = entry.Item.itemId, Quantity = entry.Quantity });
            }

            foreach (var npc in npcs)
            {
                var npcSave = new NpcSaveData
                {
                    NpcId = npc.Data != null ? npc.Data.npcId : npc.DisplayName,
                    PositionX = npc.transform.position.x,
                    PositionY = npc.transform.position.y,
                    RelationshipType = npc.State.RelationshipWithPlayer.ToString(),
                    RelationshipScore = npc.State.RelationshipScore,
                    CurrentEmotion = npc.State.CurrentEmotion.ToString(),
                    EmotionIntensity = npc.State.EmotionIntensity,
                    Money = npc.State.Money
                };

                foreach (var memory in npc.Memory.Entries)
                {
                    npcSave.Memories.Add(new MemoryEntrySave
                    {
                        Description = memory.Description,
                        Timestamp = memory.Timestamp,
                        InvolvedActors = memory.InvolvedActors,
                        EmotionalWeight = memory.EmotionalWeight,
                        Tags = memory.Tags
                    });
                }

                data.Npcs.Add(npcSave);
            }

            foreach (var obj in worldObjects)
            {
                data.WorldObjects.Add(new WorldObjectSaveData
                {
                    ObjectId = obj.ObjectId,
                    PositionX = obj.transform.position.x,
                    PositionY = obj.transform.position.y,
                    State = obj.State.ToString(),
                    OwnerId = obj.OwnerId
                });
            }

            string json = JsonUtility.ToJson(data, true);
            File.WriteAllText(SavePath, json);
            Debug.Log($"[SaveManager] Partida guardada en {SavePath}");
        }

        public SaveGameData Load()
        {
            if (!HasSaveFile) return null;
            string json = File.ReadAllText(SavePath);
            return JsonUtility.FromJson<SaveGameData>(json);
        }

        public void Apply(SaveGameData data, TimeManager time, PlayerController playerController,
            PlayerStats playerStats, InventorySystem playerInventory, ItemData[] allItems,
            NPCController[] npcs, WorldObject[] worldObjects)
        {
            if (data == null) return;

            time.LoadState(data.Time);
            playerController.TeleportTo(new Vector2(data.Player.PositionX, data.Player.PositionY));
            playerStats.LoadState(data.Player.Health, data.Player.Energy, data.Player.Money, data.Player.PowerLevel, 0f);

            var loadedInventory = data.Player.Inventory
                .Select(e => new InventoryEntry(allItems.FirstOrDefault(i => i.itemId == e.ItemId), e.Quantity))
                .Where(e => e.Item != null)
                .ToList();
            playerInventory.LoadState(loadedInventory);

            foreach (var npcSave in data.Npcs)
            {
                var npc = npcs.FirstOrDefault(n => (n.Data != null ? n.Data.npcId : n.DisplayName) == npcSave.NpcId);
                if (npc == null) continue;

                var state = new RPG.NPC.NPCState
                {
                    RelationshipWithPlayer = System.Enum.Parse<RPG.NPC.RelationshipType>(npcSave.RelationshipType),
                    RelationshipScore = npcSave.RelationshipScore,
                    CurrentEmotion = System.Enum.Parse<RPG.NPC.EmotionType>(npcSave.CurrentEmotion),
                    EmotionIntensity = npcSave.EmotionIntensity,
                    Money = npcSave.Money
                };

                var memories = npcSave.Memories.Select(m =>
                    new RPG.Memory.MemoryEntry(m.Description, m.Timestamp, m.InvolvedActors, m.EmotionalWeight, m.Tags));

                npc.LoadRuntimeState(state, memories, new Vector2(npcSave.PositionX, npcSave.PositionY));
            }

            foreach (var objSave in data.WorldObjects)
            {
                var obj = worldObjects.FirstOrDefault(o => o.ObjectId == objSave.ObjectId);
                if (obj == null) continue;

                var state = System.Enum.Parse<WorldObjectState>(objSave.State);
                obj.LoadState(state, objSave.OwnerId, new Vector2(objSave.PositionX, objSave.PositionY));
            }
        }
    }
}
