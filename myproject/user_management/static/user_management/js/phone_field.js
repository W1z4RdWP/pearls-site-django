// --- Маска для телефона +7 (XXX) XXX-XX-XX и поддержка произвольного формата ---
document.addEventListener('DOMContentLoaded', function() {
    const phoneInput = document.getElementById('id_phone_number');
    const arbitraryCheckbox = document.getElementById('id_phone_arbitrary_format');
    if (!phoneInput || !arbitraryCheckbox) return;

    // --- Маска для стандартного режима ---
    function formatPhone(value) {
        let digits = value.replace(/\D/g, '');
        if (digits.startsWith('7')) digits = digits.slice(1);
        if (digits.startsWith('8')) digits = digits.slice(1);
        digits = digits.slice(0, 10);
        if (digits.length === 0) return '';
        let result = '+7';
        if (digits.length > 0) result += ' (' + digits.slice(0, 3);
        if (digits.length >= 4) result += ') ' + digits.slice(3, 6);
        if (digits.length >= 7) result += '-' + digits.slice(6, 8);
        if (digits.length >= 9) result += '-' + digits.slice(8, 10);
        return result;
    }

    function getRawPhone(value) {
        let digits = value.replace(/\D/g, '');
        if (digits.startsWith('7')) digits = digits.slice(1);
        if (digits.startsWith('8')) digits = digits.slice(1);
        digits = digits.slice(0, 10);
        return digits.length ? '+7' + digits : '';
    }

    function setCaretToEnd() {
        setTimeout(() => {
            phoneInput.setSelectionRange(phoneInput.value.length, phoneInput.value.length);
        }, 0);
    }

    function updatePhoneMask() {
        let val = phoneInput.value;
        let formatted = formatPhone(val);
        phoneInput.value = formatted;
        setCaretToEnd();
    }

    // --- События для стандартного режима ---
    function enableMaskMode() {
        phoneInput.setAttribute('maxlength', '18');
        phoneInput.value = formatPhone(phoneInput.value);
        phoneInput.addEventListener('input', updatePhoneMaskHandler);
        phoneInput.addEventListener('focus', updatePhoneMaskHandler);
        phoneInput.addEventListener('keydown', allowFullDeleteHandler);
        phoneInput.addEventListener('keydown', plusToPlus7Handler);
    }
    function disableMaskMode() {
        phoneInput.removeAttribute('maxlength');
        phoneInput.removeEventListener('input', updatePhoneMaskHandler);
        phoneInput.removeEventListener('focus', updatePhoneMaskHandler);
        phoneInput.removeEventListener('keydown', allowFullDeleteHandler);
        phoneInput.removeEventListener('keydown', plusToPlus7Handler);
    }
    function updatePhoneMaskHandler() {
        updatePhoneMask();
    }

    function allowFullDeleteHandler(e) {
        // Разрешаем удалять всё, не блокируем Backspace/Delete
    }
    function plusToPlus7Handler(e) {
        // Если поле пустое и нажали +, подставляем +7
        if (e.key === '+' && phoneInput.value === '') {
            e.preventDefault();
            phoneInput.value = '+7';
            setCaretToEnd();
        } else if (e.key === '+' && phoneInput.selectionStart !== 0) {
            // Не даём вставить + не в начале
            e.preventDefault();
        }
        // После +7 разрешаем только цифры
        if (phoneInput.value.startsWith('+7') && !/\d/.test(e.key) && e.key.length === 1) {
            e.preventDefault();
        }
    }

    // --- События для произвольного режима ---
    function enableArbitraryMode() {
        disableMaskMode();
        phoneInput.removeAttribute('maxlength');
    }

    // --- Переключение режимов ---
    function updateMode() {
        if (arbitraryCheckbox.checked) {
            enableArbitraryMode();
        } else {
            enableMaskMode();
        }
    }

    // --- Валидация при отправке формы ---
    const form = phoneInput.closest('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            if (!arbitraryCheckbox.checked) {
                const raw = getRawPhone(phoneInput.value);
                if (raw.length !== 12) {
                    e.preventDefault();
                    let warn = form.querySelector('.um-user-warning.phone');
                    if (!warn) {
                        warn = document.createElement('div');
                        warn.className = 'um-user-warning phone';
                        warn.style.marginTop = '0';
                        phoneInput.parentNode.insertBefore(warn, phoneInput.nextSibling);
                    }
                    warn.textContent = 'Введите корректный номер телефона: 10 цифр после +7';
                    phoneInput.focus();
                }
            }
        });
    }

    // --- Сохраняем состояние чекбокса при редактировании ---
    updateMode();
    arbitraryCheckbox.addEventListener('change', updateMode);

    // Если не произвольный — сразу маска
    if (!arbitraryCheckbox.checked) {
        updatePhoneMask();
    }
});

// Phone field functionality
// This file is required for user management forms
console.log('Phone field JS loaded'); 