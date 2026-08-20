using UnityEngine;
using RPG.AI;
using RPG.Dialogue;
using RPG.Inventory;
using RPG.NPC;
using RPG.Player;
using RPG.Powers;
using RPG.SaveSystem;
using RPG.TimeSystem;
using RPG.World;

namespace RPG.Core
{
    /// <summary>
    /// Orquestador principal. Inicializa y conecta todos los sistemas y expone el punto de
    /// entrada unico para procesar la accion libre que escribe el jugador:
    /// texto -> IIntentInterpreter (interpreta) -> ActionExecutor (ejecuta) -> resultado narrativo.
    /// </summary>
    public class GameManager : MonoBehaviour
    {
        public static GameManager Instance { get; private set; }

        [Header("Referencias del jugador")]
        [SerializeField] private PlayerController playerController;
        [SerializeField] private PlayerStats playerStats;
        [SerializeField] private PlayerInteractor playerInteractor;
        [SerializeField] private InventorySystem playerInventory;
        [SerializeField] private PowerController playerPowers;

        [Header("Tiempo")]
        [SerializeField] private TimeManager timeManager;

        public TimeManager Time => timeManager;
        public DialogueSystem Dialogue { get; private set; }
        public IIntentInterpreter Interpreter { get; private set; }
        public INPCResponder NpcResponder { get; private set; }
        public ActionExecutor Executor { get; private set; }
        public SaveManager SaveManager { get; private set; }

        public event System.Action<string> OnJournalEntry;

        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }
            Instance = this;

            Dialogue = new DialogueSystem();
            Interpreter = new RuleBasedIntentInterpreter();
            NpcResponder = new RuleBasedNPCResponder();
            SaveManager = new RPG.SaveSystem.SaveManager();
            Executor = new ActionExecutor(playerStats, playerInteractor, playerInventory, playerPowers, Dialogue);

            EventBus.OnJournalEntry += HandleJournalEntry;
        }

        private void OnDestroy()
        {
            EventBus.OnJournalEntry -= HandleJournalEntry;
        }

        private void HandleJournalEntry(string text) => OnJournalEntry?.Invoke(text);

        /// <summary>Punto de entrada unico de la caja de texto libre.</summary>
        public ActionResult ProcessPlayerAction(string freeText)
        {
            if (string.IsNullOrWhiteSpace(freeText))
                return ActionResult.Fail("Escribe algo primero.");

            var context = new ActionContext
            {
                NearbyEntityNames = playerInteractor.GetNearbyNames(),
                PlayerInConversation = Dialogue.IsInConversation,
                ConversationPartnerName = Dialogue.CurrentPartner != null ? Dialogue.CurrentPartner.DisplayName : null
            };

            ActionIntent intent = Interpreter.Interpret(freeText, context);
            return Executor.Execute(intent, playerController.gameObject);
        }

        public void StartInteractionWith(NPCController npc)
        {
            var intent = new ActionIntent("") { Type = ActionType.Talk };
            npc.Interact(playerController.gameObject, intent);
        }

        public void SaveGame()
        {
            var npcs = FindObjectsByType<NPCController>(FindObjectsSortMode.None);
            var worldObjects = FindObjectsByType<WorldObject>(FindObjectsSortMode.None);
            SaveManager.Save(timeManager, playerController, playerStats, playerInventory, npcs, worldObjects);
        }

        public void LoadGame(ItemData[] allItems)
        {
            var data = SaveManager.Load();
            if (data == null) return;

            var npcs = FindObjectsByType<NPCController>(FindObjectsSortMode.None);
            var worldObjects = FindObjectsByType<WorldObject>(FindObjectsSortMode.None);
            SaveManager.Apply(data, timeManager, playerController, playerStats, playerInventory, allItems, npcs, worldObjects);
        }
    }
}
