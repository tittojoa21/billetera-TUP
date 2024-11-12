document.addEventListener('DOMContentLoaded', () => {
    autoHideAlerts(4000);
    setupTransactionConfirmation();
    formatBalances('.balance-box h3');
    setupCardInput('.credit-card-input', '.card-display');
});

/**
 * Oculta automáticamente los mensajes de alerta después de un tiempo especificado.
 * @param {number} timeout - Tiempo en milisegundos antes de ocultar las alertas.
 */
function autoHideAlerts(timeout) {
    document.querySelectorAll('.alert').forEach(alertBox => {
        setTimeout(() => fadeOut(alertBox), timeout);
    });
}

/**
 * Aplica una animación de desvanecimiento a un elemento y lo elimina.
 * @param {Element} element - Elemento a desvanecer y remover.
 * @param {number} duration - Duración en milisegundos de la animación de desvanecimiento.
 */
function fadeOut(element, duration = 500) {
    if (!element) return;
    element.style.transition = `opacity ${duration}ms ease, transform ${duration}ms ease`;
    element.style.opacity = '0';
    element.style.transform = 'translateY(-10px)';
    setTimeout(() => element?.remove(), duration);
}

/**
 * Configura la confirmación para el formulario de transacción.
 */
function setupTransactionConfirmation() {
    document.querySelectorAll('form[action*="transaction"]').forEach(form => {
        form.addEventListener('submit', handleTransactionSubmit);
    });
}

/**
 * Maneja el envío del formulario de transacción con validación y confirmación.
 * @param {Event} event - Evento de envío del formulario.
 */
function handleTransactionSubmit(event) {
    event.preventDefault();
    const form = event.target;
    const amount = parseFloat(form.amount?.value);
    const type = form.type?.value;

    if (!validateAmount(amount)) {
        showAlert("Por favor, ingresa un monto válido y positivo.", "danger");
        return;
    }

    showConfirmation(`¿Estás seguro de que deseas ${type} $${amount.toFixed(2)}?`, () => {
        form.submit();
    });
}

/**
 * Muestra una ventana de confirmación personalizada.
 * @param {string} message - Mensaje de confirmación.
 * @param {Function} onConfirm - Función a ejecutar si el usuario confirma.
 */
function showConfirmation(message, onConfirm) {
    if (confirm(message)) onConfirm();
}

/**
 * Formatea los balances en el dashboard, mostrando siempre dos decimales.
 * @param {string} selector - Selector CSS de los elementos de balance.
 */
function formatBalances(selector) {
    document.querySelectorAll(selector).forEach(balanceElement => {
        const balance = parseFloat(balanceElement.textContent.replace(/[^0-9.-]+/g, '')) || 0;
        balanceElement.textContent = `$${balance.toFixed(2)}`;
    });
}

/**
 * Configura la entrada dinámica de tarjetas de crédito con formato en tiempo real.
 * @param {string} inputSelector - Selector CSS de la entrada de la tarjeta.
 * @param {string} displaySelector - Selector CSS del elemento de visualización de la tarjeta.
 */
function setupCardInput(inputSelector, displaySelector) {
    const cardInput = document.querySelector(inputSelector);
    const cardDisplay = document.querySelector(displaySelector);

    if (cardInput && cardDisplay) {
        cardInput.addEventListener('input', () => {
            cardDisplay.textContent = formatCardNumber(cardInput.value) || '#### #### #### ####';
        });
    }
}

/**
 * Aplica formato de separación a los números de tarjeta.
 * @param {string} cardNumber - Número de tarjeta sin formato.
 * @returns {string} - Número de tarjeta formateado.
 */
function formatCardNumber(cardNumber) {
    return cardNumber.replace(/\D/g, '').replace(/(.{4})/g, '$1 ').trim();
}

/**
 * Valida que el monto ingresado sea positivo y válido.
 * @param {number} amount - Monto ingresado.
 * @returns {boolean} - Verdadero si el monto es válido y positivo.
 */
function validateAmount(amount) {
    return !isNaN(amount) && amount > 0;
}

/**
 * Muestra un mensaje de alerta en la página con opción de especificar el tipo.
 * @param {string} message - Mensaje de alerta a mostrar.
 * @param {string} type - Tipo de alerta, por defecto "danger".
 * @param {number} duration - Tiempo en milisegundos antes de ocultar automáticamente la alerta.
 */
function showAlert(message, type = "danger", duration = 4000) {
    const alertBox = createAlert(message, type);
    const alertContainer = document.querySelector('main') || document.body;

    alertContainer.prepend(alertBox);
    setTimeout(() => fadeOut(alertBox), duration);
}

/**
 * Crea un elemento de alerta basado en el mensaje y el tipo.
 * @param {string} message - Mensaje a mostrar en la alerta.
 * @param {string} type - Tipo de la alerta (ej. "success", "danger").
 * @returns {Element} - Elemento de alerta HTML.
 */
function createAlert(message, type) {
    const alertBox = document.createElement('div');
    alertBox.className = `alert alert-${type} alert-dismissible fade show`;
    alertBox.role = "alert";
    alertBox.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    return alertBox;
}
