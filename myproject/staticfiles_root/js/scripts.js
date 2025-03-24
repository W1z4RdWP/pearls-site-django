(function() {
    const animation = document.getElementById('course-completion-animation');
    if (!animation) return;

    const completionMessage = animation.querySelector('.completion-message');
    
    // Таймер для автоматического закрытия через 5 секунд
    let timeoutId = setTimeout(() => animation.remove(), 5000);

    // Закрытие при клике вне блока с сообщением
    document.addEventListener('click', function(e) {
        if (!completionMessage.contains(e.target)) {
            animation.remove();
            clearTimeout(timeoutId);
        }
    });

    // Закрытие при нажатии Esc
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            animation.remove();
            clearTimeout(timeoutId);
        }
    });
})();


// Появление карточек при доскорле до них
document.addEventListener('DOMContentLoaded', () => {
    const boxes = document.querySelectorAll('.box');
  
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('show');
        } else {
          entry.target.classList.remove('show');
        }
      });
    });
  
    boxes.forEach(box => {
      observer.observe(box);
    });
  });