using System.Collections.Generic;
using System.Text;
using UnityEngine;
using UnityEngine.UI;
using RPG.Core;
using RPG.Inventory;

namespace RPG.UI
{
    /// <summary>
    /// Coordina la UI general: el diario de sucesos (journal) y los atajos de guardado/carga.
    /// </summary>
    public class UIManager : MonoBehaviour
    {
        [SerializeField] private Text journalText;
        [SerializeField] private int maxJournalLines = 12;
        [SerializeField] private ItemData[] allItemsForLoad;

        private readonly List<string> _journalLines = new List<string>();

        private void Start()
        {
            GameManager.Instance.OnJournalEntry += HandleJournalEntry;
        }

        private void OnDestroy()
        {
            if (GameManager.Instance != null)
                GameManager.Instance.OnJournalEntry -= HandleJournalEntry;
        }

        private void Update()
        {
            if (Input.GetKeyDown(KeyCode.F5)) GameManager.Instance.SaveGame();
            if (Input.GetKeyDown(KeyCode.F9)) GameManager.Instance.LoadGame(allItemsForLoad);
        }

        private void HandleJournalEntry(string text)
        {
            _journalLines.Add(text);
            if (_journalLines.Count > maxJournalLines)
                _journalLines.RemoveAt(0);

            if (journalText == null) return;
            var sb = new StringBuilder();
            foreach (var line in _journalLines) sb.AppendLine(line);
            journalText.text = sb.ToString();
        }
    }
}
