document.addEventListener('DOMContentLoaded', function () {
    const modalElement = document.getElementById('newsGalleryModal');
    if (!modalElement || !window.bootstrap) {
      return;
    }

    const triggerSelector = '[data-news-gallery-src]';
    const triggers = Array.from(document.querySelectorAll(triggerSelector));
    if (!triggers.length) {
      return;
    }

    const modalImage = modalElement.querySelector('[data-news-gallery-image]');
    const counter = modalElement.querySelector('[data-news-gallery-counter]');
    const prevButton = modalElement.querySelector('[data-news-gallery-prev]');
    const nextButton = modalElement.querySelector('[data-news-gallery-next]');
    const modal = new bootstrap.Modal(modalElement);
    let currentIndex = 0;

    function renderImage(index) {
      const safeIndex = (index + triggers.length) % triggers.length;
      const trigger = triggers[safeIndex];

      currentIndex = safeIndex;
      modalImage.src = trigger.dataset.newsGallerySrc;
      modalImage.alt = trigger.dataset.newsGalleryAlt || '';
      counter.textContent = triggers.length > 1 ? (safeIndex + 1) + ' / ' + triggers.length : '1 / 1';

      const isSingle = triggers.length < 2;
      prevButton.hidden = isSingle;
      nextButton.hidden = isSingle;
    }

    triggers.forEach(function (trigger, index) {
      trigger.addEventListener('click', function () {
        renderImage(index);
        modal.show();
      });
    });

    prevButton.addEventListener('click', function () {
      renderImage(currentIndex - 1);
    });

    nextButton.addEventListener('click', function () {
      renderImage(currentIndex + 1);
    });

    modalElement.addEventListener('keydown', function (event) {
      if (event.key === 'ArrowLeft') {
        event.preventDefault();
        renderImage(currentIndex - 1);
      }

      if (event.key === 'ArrowRight') {
        event.preventDefault();
        renderImage(currentIndex + 1);
      }
    });

    modalElement.addEventListener('shown.bs.modal', function () {
      modalElement.focus();
    });
});