// header
document.addEventListener('DOMContentLoaded', () => {
  const hero = document.querySelector('.hero');
  const header = document.querySelector('.header');
  const scrollItems = document.querySelectorAll('.scroll-item');

	const scrollAnimation = () => {
		let windowCenter = (window.innerHeight / 2) + window.scrollY;
		scrollItems.forEach(el => {
			let scrollOffset = el.offsetTop + (el.offsetHeight / 2) + 100;
			if (windowCenter >= scrollOffset) {
				el.classList.add('animation-class');
			} else {
				el.classList.remove('animation-class');
			}
		});
	};

  const headerFixed = () => {
    let scrollTop = window.scrollY;
    let heroCenter = hero.offsetHeight / 2;
    
    if (scrollTop >= heroCenter) {
      header.classList.add('fixed');
      hero.style.marginTop = `${header.offsetHeight}px`;
    } else {
      header.classList.remove('fixed')
      hero.style.marginTop = `0px`;
    }
  }

  headerFixed();
  scrollAnimation();
  window.addEventListener('scroll', () => {
    headerFixed();
    scrollAnimation();
    
  });
});



(function() {
    const animation = document.getElementById('course-completion-animation');
    if (!animation) return;

    const completionMessage = animation.querySelector('.completion-message');
    
    // Таймер для автоматического закрытия через 5 секунд (только если нет траектории)
    let timeoutId = null;
    if (!animation.hasAttribute('data-has-trajectory')) {
        timeoutId = setTimeout(() => animation.remove(), 5000);
    }

    // Закрытие при клике вне блока с сообщением (только если нет траектории)
    document.addEventListener('click', function(e) {
        if (!completionMessage.contains(e.target) && !animation.hasAttribute('data-has-trajectory')) {
            animation.remove();
            if (timeoutId) clearTimeout(timeoutId);
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

// Раскрытие описания курса
document.addEventListener('DOMContentLoaded', () => {
  const showDescription = document.getElementById('show-description');
  const courseDescription = document.getElementById('course-description');
  const courseDescriptionImage = document.getElementById('course-description-image');
  if (!showDescription || !courseDescription) return;

  const setButtonState = (isHidden) => {
    if (isHidden) {
      showDescription.innerHTML = '<i class="fa fa-eye"></i> Показать описание';
    } else {
      showDescription.innerHTML = '<i class="fa fa-eye-slash"></i> Скрыть описание';
    }
  };

  const isCurrentlyHidden = () => {
    return window.getComputedStyle(courseDescription).display === 'none';
  };

  // Инициализация состояния кнопки в соответствии с текущей видимостью
  setButtonState(isCurrentlyHidden());

  showDescription.addEventListener('click', (e) => {
    e.preventDefault();
    const hidden = isCurrentlyHidden();
    if (hidden) {
      courseDescription.style.display = 'block';
      if (courseDescriptionImage) courseDescriptionImage.style.display = 'block';
    } else {
      courseDescription.style.display = 'none';
      if (courseDescriptionImage) courseDescriptionImage.style.display = 'none';
    }
    setButtonState(!hidden);
  });
  showDescription.style.display = 'block';
});

// Обработка заблокированных уроков
document.addEventListener('DOMContentLoaded', () => {
  const blockedLessons = document.querySelectorAll('.lesson-blocked');
  
  blockedLessons.forEach(lesson => {
    lesson.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      
      // Подсветка кнопки "Начать курс"
      const startBtn = document.getElementById('start-course-btn');
      if (startBtn) {
        startBtn.classList.add('highlight');
        startBtn.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        // Убираем подсветку через 5 секунд
        setTimeout(() => {
          startBtn.classList.remove('highlight');
        }, 5000);
      }
      
      // Показываем уведомление
      showNotification('Чтобы получить доступ к материалам, сначала начните курс');
    });
  });
});

// Функция для показа уведомлений
function showNotification(message) {
  // Удаляем предыдущее уведомление если есть
  const existingNotification = document.querySelector('.course-notification');
  if (existingNotification) {
    existingNotification.remove();
  }
  
  // Создаем новое уведомление
  const notification = document.createElement('div');
  notification.className = 'course-notification alert alert-warning';
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 1050;
    max-width: 300px;
    animation: slideInRight 0.3s ease-out;
  `;
  notification.innerHTML = `
    <i class="fa fa-exclamation-triangle"></i> ${message}
    <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
  `;
  
  document.body.appendChild(notification);
  
  // Автоматически убираем через 4 секунды
  setTimeout(() => {
    if (notification.parentElement) {
      notification.remove();
    }
  }, 4000);
}