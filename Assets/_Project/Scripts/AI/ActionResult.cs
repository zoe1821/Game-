namespace RPG.AI
{
    /// <summary>Resultado narrativo de ejecutar una accion. Lo genera siempre el motor, nunca la IA en solitario.</summary>
    public class ActionResult
    {
        public bool Success;
        public string Message;

        public static ActionResult Ok(string message) => new ActionResult { Success = true, Message = message };
        public static ActionResult Fail(string message) => new ActionResult { Success = false, Message = message };
    }
}
