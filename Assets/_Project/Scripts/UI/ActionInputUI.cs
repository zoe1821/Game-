using UnityEngine;
using UnityEngine.UI;
using RPG.Core;
using RPG.Player;

namespace RPG.UI
{
    /// <summary>
    /// La caja de texto libre: el corazon del juego. El jugador escribe cualquier accion
    /// ("uso telequinesis para lanzar el sillon...") y este componente la envia al GameManager,
    /// que la interpreta y la ejecuta a traves de todo el pipeline de IA -> motor.
    /// </summary>
    public class ActionInputUI : MonoBehaviour
    {
        [SerializeField] private InputField inputField;
        [SerializeField] private Button sendButton;
        [SerializeField] private Text feedbackText;
        [SerializeField] private PlayerController playerController;

        private void Awake()
        {
            if (sendButton != null) sendButton.onClick.AddListener(SubmitAction);
            if (inputField != null) inputField.onEndEdit.AddListener(OnEndEdit);
        }

        private void Update()
        {
            // Desactiva el movimiento con WASD mientras el jugador esta escribiendo.
            if (playerController != null && inputField != null)
                playerController.InputEnabled = !inputField.isFocused;
        }

        private void OnEndEdit(string text)
        {
            if (Input.GetKeyDown(KeyCode.Return) || Input.GetKeyDown(KeyCode.KeypadEnter))
                SubmitAction();
        }

        public void SubmitAction()
        {
            if (inputField == null || string.IsNullOrWhiteSpace(inputField.text)) return;

            string text = inputField.text;
            inputField.text = "";

            var result = GameManager.Instance.ProcessPlayerAction(text);
            if (feedbackText != null)
                feedbackText.text = result.Message;
        }
    }
}
