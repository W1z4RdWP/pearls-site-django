// Автоматически добавляем target="_blank" ко всем ссылкам в блоке .lesson-content
function addTargetBlankToLessonLinks() {
    const lessonContent = document.querySelector('.lesson-content');
    if (lessonContent) {
        const links = lessonContent.querySelectorAll('a[href]');
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
document.addEventListener('DOMContentLoaded', addTargetBlankToLessonLinks);

// Также вызываем при динамическом обновлении контента урока
const originalFetch = window.fetch;
window.fetch = function(...args) {
    return originalFetch.apply(this, args).then(response => {
        // Если это запрос к уроку, добавляем обработчик для обновления ссылок
        if (args[0] && typeof args[0] === 'string' && args[0].includes('/courses/') && args[0].includes('/lesson/')) {
            setTimeout(addTargetBlankToLessonLinks, 100);
        }
        return response;
    });
};