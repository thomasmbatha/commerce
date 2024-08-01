document.addEventListener('DOMContentLoaded', () => {
    const inputs = document.querySelectorAll('.input-field input');

    inputs.forEach(input => {
        // Initial check to apply 'not-empty' class if the input has a value (including autofilled)
        if (input.value) {
            input.classList.add('not-empty');
        }

        // Listen for input events to dynamically add/remove 'not-empty' class
        input.addEventListener('input', () => {
            if (input.value) {
                input.classList.add('not-empty');
            } else {
                input.classList.remove('not-empty');
            }
        });

        // Handle browser autofill detection (especially in Chrome)
        input.addEventListener('animationstart', (event) => {
            if (event.animationName === 'onAutoFillStart') {
                input.classList.add('not-empty');
            }
        });

        // Fallback for detecting changes in input state
        input.addEventListener('change', () => {
            if (input.value) {
                input.classList.add('not-empty');
            } else {
                input.classList.remove('not-empty');
            }
        });
    });
});
