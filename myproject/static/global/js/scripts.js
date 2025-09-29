// header
document.addEventListener('DOMContentLoaded', () => {
  const hero = document.querySelector('.hero-landing');
  const header = document.querySelector('.header');
  const scrollItems = document.querySelectorAll('.scroll-item');
  
  // Добавляем класс для хедера сразу
  header.classList.add('always-visible');
  
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
    
    if (hero) {
      let heroCenter = hero.offsetHeight / 2;
      
      if (scrollTop >= heroCenter) {
        header.classList.add('fixed');
      } else {
        header.classList.remove('fixed');
      }
    } else {
      if (scrollTop > 100) {
        header.classList.add('fixed');
      } else {
        header.classList.remove('fixed');
      }
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


// Переключение темы
document.addEventListener('DOMContentLoaded', function() {
  const btn = document.getElementById('theme-toggle-btn');
  const logo = document.getElementById('logopng');
  const footerLogo = document.getElementById('footerlogo');
  const footerLogoMobile = document.getElementById('footerlogomobile');

  // Определяем пути к логотипам
  const darkLogo = "/static/global/imgs/logo_lc.png";
  const lightLogo = "/static/global/imgs/logo_light_theme.png";
  
  function updateLogo() {
    if (document.body.classList.contains('theme-dark')) {
      if (logo) logo.src = darkLogo;
      if (footerLogo) footerLogo.src = darkLogo;
      if (footerLogoMobile) footerLogoMobile.src = darkLogo;
    } else {
      if (logo) logo.src = lightLogo;
      if (footerLogo) footerLogo.src = lightLogo;
      if (footerLogoMobile) footerLogoMobile.src = lightLogo;
    }
  }
  
  if (btn) {
    const icon = btn.querySelector('i');
    
    function updateIcon() {
      if (document.body.classList.contains('theme-dark')) {
        icon.className = 'fa-solid fa-sun';
        btn.title = 'Переключить на светлую тему';
      } else {
        icon.className = 'fa-solid fa-moon';
        btn.title = 'Переключить на темную тему';
      }
    }
    
    btn.addEventListener('click', function() {
      document.body.classList.toggle('theme-dark');
      localStorage.setItem('theme', document.body.classList.contains('theme-dark') ? 'dark' : 'light');
      updateLogo();
      updateIcon();
    });
    
    // Инициализация при загрузке
    if (localStorage.getItem('theme') === 'dark') {
      document.body.classList.add('theme-dark');
    }
    updateIcon();
    updateLogo();
  }
});

// Глобальная подмена "битых" изображений на заглушку
// Убрал, так как нет необходимости, восстановить если будет картинка
// document.addEventListener('DOMContentLoaded', () => {
//   const FALLBACK_SRC = '/static/global/imgs/img-fallback.svg';

//   function applyFallback(img) {
//     if (!img || img.dataset.fallbackApplied) return;
//     img.dataset.fallbackApplied = '1';
//     img.src = FALLBACK_SRC;
//     img.classList.add('img-fallback');
//   }

//   function wireImage(img) {
//     if (!img || img.dataset.fallbackWired) return;
//     img.dataset.fallbackWired = '1';
//     img.addEventListener('error', () => applyFallback(img), { once: true });
//     // Уже сломано к моменту навешивания?
//     if (img.complete && img.naturalWidth === 0) applyFallback(img);
//   }

//   // Инициализация на существующих картинках
//   document.querySelectorAll('img, .lesson-content img, img[data-use-fallback]')
//     .forEach(wireImage);

//   // Реакция на динамически добавленные изображения (например, из редактора)
//   const mo = new MutationObserver((mutations) => {
//     for (const m of mutations) {
//       m.addedNodes && m.addedNodes.forEach(node => {
//         if (node && node.tagName === 'IMG') {
//           wireImage(node);
//         } else if (node && node.querySelectorAll) {
//           node.querySelectorAll('img').forEach(wireImage);
//         }
//       });
//     }
//   });
//   mo.observe(document.body, { childList: true, subtree: true });
// });

