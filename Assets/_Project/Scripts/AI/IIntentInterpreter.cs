using System.Collections.Generic;

namespace RPG.AI
{
    /// <summary>
    /// Contexto que el motor entrega al interprete para ayudarle a resolver referencias
    /// ("la silla", "Sarah") sin que el interprete necesite tocar objetos reales del mundo.
    /// </summary>
    public class ActionContext
    {
        public IEnumerable<string> NearbyEntityNames = System.Array.Empty<string>();
        public bool PlayerInConversation;
        public string ConversationPartnerName;
    }

    /// <summary>
    /// Interpreta texto libre del jugador y produce una intencion (ActionIntent).
    /// NUNCA modifica el estado del juego: solo interpreta. Implementaciones futuras
    /// pueden delegar en un modelo de lenguaje (LLM) real manteniendo este mismo contrato,
    /// de forma que el motor (ActionExecutor) no necesita cambiar.
    /// </summary>
    public interface IIntentInterpreter
    {
        ActionIntent Interpret(string freeText, ActionContext context);
    }
}
