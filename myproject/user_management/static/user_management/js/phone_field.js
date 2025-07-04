// --- Кастомное поле телефона с +7 и чекбоксом "Произвольный формат" ---
document.addEventListener('DOMContentLoaded', function() {
    const phoneInput = document.getElementById('id_phone_number');
    const arbitraryCheckbox = document.getElementById('arbitrary_format_checkbox');
    if (!phoneInput || !arbitraryCheckbox) return;

    function setDefaultPhone() {
        if (!phoneInput.value.startsWith('+7')) {
            phoneInput.value = '+7';
        }
        setCaretToEnd();
    }
    function setCaretToEnd() {
        setTimeout(() => {
            phoneInput.setSelectionRange(phoneInput.value.length, phoneInput.value.length);
        }, 0);
    }
    function enforceFormat() {
        let val = phoneInput.value;
        if (!val.startsWith('+7')) val = '+7' + val.replace(/^[^\d]*/, '');
        val = val.replace(/[^\d+]/g, '');
        if (val.length > 12) val = val.slice(0, 12);
        phoneInput.value = val;
        if (!phoneInput.value.startsWith('+7')) setDefaultPhone();
    }
    phoneInput.addEventListener('focus', function() {
        if (!arbitraryCheckbox.checked) setDefaultPhone();
    });
    phoneInput.addEventListener('input', function() {
        if (arbitraryCheckbox.checked) return;
        enforceFormat();
    });
    phoneInput.addEventListener('keydown', function(e) {
        if (arbitraryCheckbox.checked) return;
        // Запретить удалять +7
        if ((phoneInput.selectionStart <= 2) && (e.key === 'Backspace' || e.key === 'Delete')) {
            e.preventDefault();
        }
        // Запретить ввод перед +7
        if (phoneInput.selectionStart < 2 && e.key.length === 1) {
            e.preventDefault();
        }
    });
    arbitraryCheckbox.addEventListener('change', function() {
        if (arbitraryCheckbox.checked) {
            phoneInput.removeAttribute('maxlength');
        } else {
            setDefaultPhone();
            phoneInput.setAttribute('maxlength', '12');
        }
    });
    // Если поле уже заполнено (редактирование) и не в произвольном режиме
    if (!arbitraryCheckbox.checked) setDefaultPhone();

    // --- Валидация при отправке формы ---
    const form = phoneInput.closest('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            if (!arbitraryCheckbox.checked && phoneInput.value.length < 12) {
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
        });
    }
}); 