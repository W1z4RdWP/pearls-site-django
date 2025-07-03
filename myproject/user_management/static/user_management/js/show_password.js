// --- Показ/скрытие пароля ---
document.addEventListener('DOMContentLoaded', function() {
    const passwordInputs = document.querySelectorAll('input[type="password"], input[type="text"][name*="password"]');
    if (!passwordInputs.length) return;

    passwordInputs.forEach(function(passwordInput) {
          // SVG для открытого и закрытого глаза
    const eyeOpen = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" style="vertical-align:middle;" fill="none" stroke="#555" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="12" rx="9" ry="5"/><circle cx="12" cy="12" r="2"/></svg>`;
    const eyeClosed = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" style="vertical-align:middle;" fill="none" stroke="#555" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="12" rx="9" ry="5"/><path d="M3 3l18 18"/></svg>`;

    // Обёртка для позиционирования
    const wrapper = document.createElement('div');
    wrapper.style.position = 'relative';
    passwordInput.parentNode.insertBefore(wrapper, passwordInput);
    wrapper.appendChild(passwordInput);

    // Кнопка-глаз
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.innerHTML = eyeClosed;
    btn.style.position = 'absolute';
    btn.style.right = '8px';
    btn.style.top = '50%';
    btn.style.transform = 'translateY(-50%)';
    btn.style.border = 'none';
    btn.style.background = 'none';
    btn.style.cursor = 'pointer';
    btn.style.padding = '0';
    btn.style.height = '24px';
    btn.style.width = '24px';

    wrapper.appendChild(btn);

    let shown = false;
    btn.addEventListener('click', function(e) {
        e.preventDefault();
        shown = !shown;
        passwordInput.type = shown ? 'text' : 'password';
        btn.innerHTML = shown ? eyeOpen : eyeClosed;
    });
    })
  
});
