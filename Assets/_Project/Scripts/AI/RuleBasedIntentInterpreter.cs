using System;
using System.Globalization;
using System.Linq;
using System.Text;

namespace RPG.AI
{
    /// <summary>
    /// Interprete de acciones libres basado en reglas y palabras clave (sin conexion externa).
    /// Es la implementacion por defecto de IIntentInterpreter para que el juego funcione
    /// completamente offline en la Fase 1. Mas adelante se puede anadir una implementacion
    /// que delegue en un modelo de lenguaje real (por ejemplo la API de Claude) sin tocar
    /// ningun otro sistema, porque todos dependen solo de la interfaz IIntentInterpreter.
    /// </summary>
    public class RuleBasedIntentInterpreter : IIntentInterpreter
    {
        private static readonly string[] PowerKeywords = { "telequinesis", "telekinesis", "quinesis" };
        private static readonly string[] AskKeywords = { "pregunto", "preguntar", "le pregunto" };
        private static readonly string[] TalkKeywords = { "digo", "le digo", "cuento", "hablo", "le hablo", "converso" };
        private static readonly string[] LieKeywords = { "miento", "mentira", "le miento" };
        private static readonly string[] StealKeywords = { "robo", "hurto", "le quito" };
        private static readonly string[] PushKeywords = { "empujo", "empujar" };
        private static readonly string[] ThrowKeywords = { "lanzo", "tiro", "arrojo" };
        private static readonly string[] TakeKeywords = { "cojo", "tomo", "agarro", "recojo", "levanto" };
        private static readonly string[] DropKeywords = { "suelto", "dejo caer" };
        private static readonly string[] BreakKeywords = { "rompo", "destrozo", "destruyo" };
        private static readonly string[] OpenKeywords = { "abro" };
        private static readonly string[] CloseKeywords = { "cierro" };
        private static readonly string[] HideKeywords = { "escondo", "me oculto" };
        private static readonly string[] EscapeKeywords = { "salgo corriendo", "huyo", "escapo" };
        private static readonly string[] RunKeywords = { "corro" };
        private static readonly string[] JumpKeywords = { "salto" };
        private static readonly string[] SitKeywords = { "me siento", "sentarme" };
        private static readonly string[] LieDownKeywords = { "me acuesto", "acostarme", "recostarme" };
        private static readonly string[] AttackKeywords = { "ataco", "golpeo", "peleo", "pego" };
        private static readonly string[] HelpKeywords = { "ayudo", "socorro" };
        private static readonly string[] UseKeywords = { "uso", "utilizo" };
        private static readonly string[] MoveKeywords = { "voy a", "camino hacia", "me dirijo" };

        public ActionIntent Interpret(string freeText, ActionContext context)
        {
            var intent = new ActionIntent(freeText) { Content = freeText };
            if (string.IsNullOrWhiteSpace(freeText)) return intent;

            string normalized = Normalize(freeText);

            // La telequinesis (u otro poder futuro) tiene prioridad: "uso telequinesis para lanzar..."
            if (ContainsAny(normalized, PowerKeywords))
            {
                intent.Type = ActionType.UsePower;
                intent.PowerName = "telequinesis";
                intent.Content = ResolveTelekinesisSubVerb(normalized);
            }
            else if (ContainsAny(normalized, AskKeywords)) intent.Type = ActionType.Ask;
            else if (ContainsAny(normalized, LieKeywords)) intent.Type = ActionType.Lie;
            else if (ContainsAny(normalized, StealKeywords)) intent.Type = ActionType.Steal;
            else if (ContainsAny(normalized, TalkKeywords)) intent.Type = ActionType.Talk;
            else if (ContainsAny(normalized, EscapeKeywords)) intent.Type = ActionType.Escape;
            else if (ContainsAny(normalized, PushKeywords)) intent.Type = ActionType.Push;
            else if (ContainsAny(normalized, ThrowKeywords)) intent.Type = ActionType.Throw;
            else if (ContainsAny(normalized, DropKeywords)) intent.Type = ActionType.Drop;
            else if (ContainsAny(normalized, TakeKeywords)) intent.Type = ActionType.Take;
            else if (ContainsAny(normalized, BreakKeywords)) intent.Type = ActionType.Break;
            else if (ContainsAny(normalized, OpenKeywords)) intent.Type = ActionType.Open;
            else if (ContainsAny(normalized, CloseKeywords)) intent.Type = ActionType.Close;
            else if (ContainsAny(normalized, HideKeywords)) intent.Type = ActionType.Hide;
            else if (ContainsAny(normalized, SitKeywords)) intent.Type = ActionType.Sit;
            else if (ContainsAny(normalized, LieDownKeywords)) intent.Type = ActionType.LieDown;
            else if (ContainsAny(normalized, JumpKeywords)) intent.Type = ActionType.Jump;
            else if (ContainsAny(normalized, RunKeywords)) intent.Type = ActionType.Run;
            else if (ContainsAny(normalized, AttackKeywords)) intent.Type = ActionType.Attack;
            else if (ContainsAny(normalized, HelpKeywords)) intent.Type = ActionType.Help;
            else if (ContainsAny(normalized, UseKeywords)) intent.Type = ActionType.Use;
            else if (ContainsAny(normalized, MoveKeywords)) intent.Type = ActionType.Move;
            else intent.Type = ActionType.Unknown;

            intent.TargetName = ResolveTarget(normalized, context);
            return intent;
        }

        private static readonly string[] ThrowSubVerbs = { "lanzar", "lanza", "lanzo", "tirar", "tiro", "arrojar", "arrojo" };
        private static readonly string[] PushSubVerbs = { "empujar", "empujo", "aleja", "alejar" };
        private static readonly string[] PullSubVerbs = { "atraer", "atrae", "acercar", "acerca", "jalar", "jalo" };

        private static string ResolveTelekinesisSubVerb(string normalizedText)
        {
            if (ContainsAny(normalizedText, ThrowSubVerbs)) return "lanzar";
            if (ContainsAny(normalizedText, PushSubVerbs)) return "empujar";
            if (ContainsAny(normalizedText, PullSubVerbs)) return "atraer";
            return "levantar";
        }

        private static string ResolveTarget(string normalizedText, ActionContext context)
        {
            if (context?.NearbyEntityNames == null) return null;

            string best = null;
            foreach (var name in context.NearbyEntityNames)
            {
                string normalizedName = Normalize(name);
                if (normalizedText.Contains(normalizedName))
                {
                    if (best == null || normalizedName.Length > Normalize(best).Length)
                        best = name;
                }
            }
            return best;
        }

        private static bool ContainsAny(string normalizedText, string[] keywords) =>
            keywords.Any(k => normalizedText.Contains(Normalize(k)));

        private static string Normalize(string text)
        {
            if (string.IsNullOrEmpty(text)) return string.Empty;
            string lower = text.ToLowerInvariant();
            string formD = lower.Normalize(NormalizationForm.FormD);
            var sb = new StringBuilder();
            foreach (char c in formD)
            {
                var category = CharUnicodeInfo.GetUnicodeCategory(c);
                if (category != UnicodeCategory.NonSpacingMark)
                    sb.Append(c);
            }
            return sb.ToString().Normalize(NormalizationForm.FormC);
        }
    }
}
