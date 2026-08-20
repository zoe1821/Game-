using System;
using System.Collections.Generic;
using RPG.NPC;

namespace RPG.Dialogue
{
    /// <summary>Gestiona la conversacion activa entre el jugador y un NPC.</summary>
    public class DialogueSystem
    {
        public NPCController CurrentPartner { get; private set; }
        public List<DialogueLine> Log { get; } = new List<DialogueLine>();
        public bool IsInConversation => CurrentPartner != null;

        public event Action<NPCController> OnConversationStarted;
        public event Action OnConversationEnded;
        public event Action<DialogueLine> OnLineAdded;

        public void StartConversation(NPCController partner)
        {
            if (partner == null) return;
            CurrentPartner = partner;
            Log.Clear();
            OnConversationStarted?.Invoke(partner);
        }

        public void EndConversation()
        {
            if (!IsInConversation) return;
            CurrentPartner = null;
            OnConversationEnded?.Invoke();
        }

        public void AddPlayerLine(string text)
        {
            if (!IsInConversation) return;
            var line = new DialogueLine("Tu", text, true);
            Log.Add(line);
            OnLineAdded?.Invoke(line);
        }

        public void AddNpcLine(string speakerName, string text)
        {
            if (!IsInConversation) return;
            var line = new DialogueLine(speakerName, text, false);
            Log.Add(line);
            OnLineAdded?.Invoke(line);
        }
    }
}
