document.querySelectorAll('.input-field input').forEach(input => {
    input.addEventListener('input', () => {
        if (input.value) {
            input.classList.add('not-empty');
        } else {
            input.classList.remove('not-empty');
        }
    });
});
