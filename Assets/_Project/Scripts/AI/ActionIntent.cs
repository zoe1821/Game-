namespace RPG.AI
{
    /// <summary>
    /// Categorias de accion que el interprete puede reconocer en un texto libre.
    /// Esta lista se puede ampliar sin romper nada: una accion no reconocida cae en Unknown
    /// y el ActionExecutor respondera de forma natural explicando que no sabe interpretarla.
    /// </summary>
    public enum ActionType
    {
        Unknown,
        Move,
        Talk,
        Ask,
        Lie,
        Take,
        Drop,
        Push,
        Throw,
        Break,
        Open,
        Close,
        Hide,
        Run,
        Jump,
        Sit,
        LieDown,
        UsePower,
        Steal,
        Attack,
        Escape,
        Use,
        Help
    }

    /// <summary>
    /// Intencion interpretada a partir del texto libre del jugador. Es SOLO una interpretacion:
    /// no modifica ningun estado del juego por si misma. El ActionExecutor decide si es
    /// posible y, en tal caso, ejecuta el cambio real en el motor.
    /// </summary>
    public class ActionIntent
    {
        public string RawText;
        public ActionType Type = ActionType.Unknown;

        /// <summary>Nombre del objetivo tal como aparece/se detecto en el texto (NPC u objeto). Puede ser null.</summary>
        public string TargetName;

        /// <summary>Nombre del poder mencionado, si lo hay (ej. "telequinesis").</summary>
        public string PowerName;

        /// <summary>Texto libre adicional relevante (lo que se dice, la pregunta, etc.).</summary>
        public string Content;

        public ActionIntent(string rawText)
        {
            RawText = rawText;
        }
    }
}
