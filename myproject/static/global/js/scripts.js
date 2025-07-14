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
    if (!hero) return;
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

  // const darkLogo = "{% static 'global/imgs/logo_lc.png' %}";
  // const lightLogo = "{% static 'global/imgs/logo_light_theme.png' %}";
  
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
  if (btn && (logo || footerLogo || footerLogoMobile)) {
    btn.addEventListener('click', function() {
      document.body.classList.toggle('theme-dark');
      btn.textContent = document.body.classList.contains('theme-dark') ? 'Тёмная тема' : 'Светлая тема';
      localStorage.setItem('theme', document.body.classList.contains('theme-dark') ? 'dark' : 'light');
      updateLogo();
    });
    if (localStorage.getItem('theme') === 'dark') {
      document.body.classList.add('theme-dark');
      btn.textContent = 'Тёмная тема';
      updateLogo();
    } else {
      updateLogo();
    }
  }
});

