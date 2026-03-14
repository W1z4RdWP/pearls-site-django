    // Автоматически добавляем target="_blank" ко всем ссылкам в блоке .detail
    function addTargetBlankToLinks() {
        const detailBlock = document.querySelector('.detail');
        if (detailBlock) {
            const links = detailBlock.querySelectorAll('a[href]');
            links.forEach(link => {
                // Проверяем, что ссылка ведет на внешний сайт (не относительная)
                const href = link.getAttribute('href');
                if (href && (href.startsWith('http://') || href.startsWith('https://') || href.startsWith('//'))) {
                    link.setAttribute('target', '_blank');
                    link.setAttribute('rel', 'noopener noreferrer');
                }
            });
        }
    }

    // Вызываем функцию при загрузке страницы
    document.addEventListener('DOMContentLoaded', addTargetBlankToLinks);

    // Также вызываем при AJAX-загрузке контента урока
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        return originalFetch.apply(this, args).then(response => {
            // Если это запрос к уроку, добавляем обработчик для обновления ссылок
            if (args[0] && typeof args[0] === 'string' && args[0].includes('/builder/lesson/') && args[0].includes('/?ajax=1')) {
                setTimeout(addTargetBlankToLinks, 100);
            }
            return response;
        });
    };
