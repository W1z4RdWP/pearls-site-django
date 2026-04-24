/**
 * Пока не загружен веб-шрифт Font Awesome, в шапке видны эмодзи из разметки (.nav-icon-slot__emoji).
 * После проверки document.fonts — класс nav-fa-ready на <html>.
 */
(function initNavFontAwesomeReady() {
  function faNavFontsLikelyLoaded() {
    if (!document.fonts || typeof document.fonts.check !== 'function') {
      return false;
    }
    try {
      return (
        document.fonts.check('900 1em "Font Awesome 6 Free"') ||
        document.fonts.check('400 1em "Font Awesome 6 Brands"')
      );
    } catch (e) {
      return false;
    }
  }
  function markReady() {
    document.documentElement.classList.add('nav-fa-ready');
  }
  function pollUntilReady() {
    const started = Date.now();
    const maxMs = 45000;
    const tick = () => {
      if (faNavFontsLikelyLoaded()) {
        markReady();
        return;
      }
      if (Date.now() - started >= maxMs) {
        return;
      }
      setTimeout(tick, 250);
    };
    tick();
  }
  function run() {
    if (faNavFontsLikelyLoaded()) {
      markReady();
      return;
    }
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready
        .then(() => {
          requestAnimationFrame(() => {
            if (faNavFontsLikelyLoaded()) {
              markReady();
            } else {
              pollUntilReady();
            }
          });
        })
        .catch(() => pollUntilReady());
    } else {
      pollUntilReady();
    }
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }
})();

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
