using System;

namespace RPG.Dialogue
{
    [Serializable]
    public class DialogueLine
    {
        public string SpeakerName;
        public string Text;
        public bool IsPlayer;

        public DialogueLine(string speakerName, string text, bool isPlayer)
        {
            SpeakerName = speakerName;
            Text = text;
            IsPlayer = isPlayer;
        }
    }
}
