using System.Text;
using UnityEngine;
using UnityEngine.UI;
using RPG.Core;
using RPG.Dialogue;
using RPG.NPC;

namespace RPG.UI
{
    /// <summary>Panel que muestra la conversacion activa con un NPC.</summary>
    public class DialogueUI : MonoBehaviour
    {
        [SerializeField] private GameObject panelRoot;
        [SerializeField] private Text speakerNameText;
        [SerializeField] private Text logText;

        private DialogueSystem _dialogue;

        private void Start()
        {
            _dialogue = GameManager.Instance.Dialogue;
            _dialogue.OnConversationStarted += HandleStarted;
            _dialogue.OnConversationEnded += HandleEnded;
            _dialogue.OnLineAdded += HandleLineAdded;

            if (panelRoot != null) panelRoot.SetActive(false);
        }

        private void OnDestroy()
        {
            if (_dialogue == null) return;
            _dialogue.OnConversationStarted -= HandleStarted;
            _dialogue.OnConversationEnded -= HandleEnded;
            _dialogue.OnLineAdded -= HandleLineAdded;
        }

        private void HandleStarted(NPCController npc)
        {
            if (panelRoot != null) panelRoot.SetActive(true);
            if (speakerNameText != null) speakerNameText.text = npc.DisplayName;
            RefreshLog();
        }

        private void HandleEnded()
        {
            if (panelRoot != null) panelRoot.SetActive(false);
        }

        private void HandleLineAdded(DialogueLine line) => RefreshLog();

        private void RefreshLog()
        {
            if (logText == null) return;
            var sb = new StringBuilder();
            foreach (var line in _dialogue.Log)
                sb.AppendLine($"{line.SpeakerName}: {line.Text}");
            logText.text = sb.ToString();
        }
    }
}
