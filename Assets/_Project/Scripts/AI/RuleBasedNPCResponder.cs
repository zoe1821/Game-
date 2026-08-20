using UnityEngine;
using RPG.NPC;

namespace RPG.AI
{
    /// <summary>
    /// Generador de respuestas de NPC basado en reglas simples (personalidad + relacion + emocion).
    /// Implementacion por defecto para que el juego sea jugable sin depender de un servicio externo.
    /// Sustituible por una implementacion basada en un LLM real sin cambiar el resto del motor.
    /// </summary>
    public class RuleBasedNPCResponder : INPCResponder
    {
        public string GenerateResponse(NPCController npc, ActionIntent intent, ActionResult result)
        {
            if (npc?.Data == null) return result?.Message ?? "...";

            if (!result.Success)
                return Pick(npc, $"({result.Message})");

            return intent.Type switch
            {
                ActionType.Steal => Pick(npc,
                    "¡Oye! ¡Eso es mio!",
                    "¿Que crees que estas haciendo?",
                    npc.Data.bravery > 0.6f ? "¡Devuelveme eso ahora mismo!" : "N-no puedes hacer eso..."),

                ActionType.Push or ActionType.Attack => Pick(npc,
                    npc.Data.bravery > 0.6f ? "¡No te tengo miedo!" : "¡Aléjate de mi!",
                    "¿Por que hiciste eso?"),

                ActionType.Lie => Pick(npc,
                    npc.Data.intelligence > 0.6f ? "No te creo ni una palabra." : "Ah... vale.",
                    "Hmm, eso suena raro."),

                ActionType.Ask => Pick(npc,
                    "Buena pregunta, dejame pensarlo.",
                    $"No se, {(npc.State.RelationshipScore > 20 ? "pero contigo puedo hablar de esto" : "apenas te conozco")}.",
                    "Depende de por que lo preguntas."),

                ActionType.Talk => Pick(npc,
                    "Te escucho.",
                    "Interesante...",
                    npc.State.RelationshipScore > 20 ? "Sabes que puedes confiar en mi, ¿no?" : "Vale."),

                ActionType.Help => Pick(npc,
                    "Gracias, de verdad lo necesitaba.",
                    "No tenias que hacerlo, pero te lo agradezco."),

                ActionType.UsePower => Pick(npc,
                    "¡¿Que fue eso?!",
                    "¡Eso no es normal!",
                    npc.Data.bravery > 0.7f ? "Interesante truco... ¿como lo hiciste?" : "¡Aléjate de mi!"),

                ActionType.Hide => Pick(npc, "¿Donde se metio?"),

                _ => Pick(npc, "...", "No estoy segura de que quieres decir.")
            };
        }

        private static string Pick(NPCController npc, params string[] options)
        {
            if (options.Length == 0) return "...";
            int index = Random.Range(0, options.Length);
            return options[index];
        }
    }
}
