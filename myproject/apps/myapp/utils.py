import bleach
import re

def clean_rutube_iframe(html: str) -> str:
    """
    Очищает HTML контент, сохраняя стандартные теги форматирования
    и разрешая только iframe с Rutube.
    """
    # Стандартные теги для форматирования текста из CKEditor
    ALLOWED_TAGS = [
        # Блочные элементы
        'p', 'div', 'br', 'hr',
        # Заголовки
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        # Форматирование текста
        'strong', 'b', 'em', 'i', 'u', 's', 'strike', 'del', 'ins',
        'sub', 'sup', 'mark', 'small', 'big',
        # Списки
        'ul', 'ol', 'li',
        # Таблицы
        'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td', 'caption', 'colgroup', 'col',
        # Цитаты и код
        'blockquote', 'pre', 'code',
        # Ссылки и изображения
        'a', 'img', 'figure', 'figcaption',
        # Медиа
        'iframe', 'video', 'audio', 'source',
        # Прочее
        'span', 'abbr', 'address', 'cite', 'q',
    ]
    
    # Разрешённые атрибуты для тегов
    ALLOWED_ATTRIBUTES = {
        '*': ['class', 'id', 'style', 'title', 'dir', 'lang'],
        'a': ['href', 'target', 'rel', 'name'],
        'img': ['src', 'alt', 'width', 'height', 'loading'],
        'table': ['border', 'cellpadding', 'cellspacing', 'width', 'height'],
        'th': ['colspan', 'rowspan', 'scope', 'width', 'height'],
        'td': ['colspan', 'rowspan', 'width', 'height'],
        'col': ['span', 'width'],
        'colgroup': ['span'],
        'iframe': ['src', 'frameborder', 'allow', 'allowfullscreen', 'width', 'height'],
        'video': ['src', 'controls', 'width', 'height', 'poster', 'autoplay', 'loop', 'muted'],
        'audio': ['src', 'controls', 'autoplay', 'loop', 'muted'],
        'source': ['src', 'type'],
        'ol': ['start', 'type', 'reversed'],
        'li': ['value'],
        'blockquote': ['cite'],
        'q': ['cite'],
        'abbr': ['title'],
    }
    
    # Очищаем HTML с разрешёнными тегами и атрибутами
    cleaned = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=False,
        strip_comments=True
    )
    
    # Удаляем iframe с недопустимыми src (не Rutube)
    # Используем регулярное выражение для фильтрации iframe
    def filter_iframes(match):
        iframe_html = match.group(0)
        # Проверяем, содержит ли iframe src с Rutube
        if 'src="https://rutube.ru/play/embed/' in iframe_html or "src='https://rutube.ru/play/embed/" in iframe_html:
            return iframe_html
        # Если нет - удаляем iframe
        return ''
    
    cleaned = re.sub(r'<iframe[^>]*>.*?</iframe>', filter_iframes, cleaned, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r'<iframe[^>]*/>', filter_iframes, cleaned, flags=re.IGNORECASE)
    
    return cleaned