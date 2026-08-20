using UnityEngine;

namespace RPG.Player
{
    /// <summary>Movimiento 2D del jugador usando fisica (Rigidbody2D), en 8 direcciones.</summary>
    [RequireComponent(typeof(Rigidbody2D))]
    public class PlayerController : MonoBehaviour
    {
        [SerializeField] private float moveSpeed = 4.5f;
        [SerializeField] private bool inputEnabled = true;

        private Rigidbody2D _rb;
        private Vector2 _moveInput;

        public Vector2 FacingDirection { get; private set; } = Vector2.down;

        /// <summary>Se desactiva mientras el jugador esta en un dialogo o escribiendo una accion.</summary>
        public bool InputEnabled
        {
            get => inputEnabled;
            set => inputEnabled = value;
        }

        private void Awake()
        {
            _rb = GetComponent<Rigidbody2D>();
            _rb.gravityScale = 0f;
            _rb.freezeRotation = true;
        }

        private void Update()
        {
            if (!inputEnabled)
            {
                _moveInput = Vector2.zero;
                return;
            }

            _moveInput.x = Input.GetAxisRaw("Horizontal");
            _moveInput.y = Input.GetAxisRaw("Vertical");
            _moveInput = Vector2.ClampMagnitude(_moveInput, 1f);

            if (_moveInput.sqrMagnitude > 0.01f)
                FacingDirection = _moveInput.normalized;
        }

        private void FixedUpdate()
        {
            _rb.velocity = _moveInput * moveSpeed;
        }

        public void TeleportTo(Vector2 position)
        {
            _rb.position = position;
        }
    }
}
