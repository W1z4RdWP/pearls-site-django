import bleach
from bleach.css_sanitizer import CSSSanitizer
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
    
    # Разрешённые CSS свойства для сохранения форматирования из CKEditor5
    ALLOWED_CSS_PROPERTIES = [
        # Шрифты
        'font-size', 'font-family', 'font-weight', 'font-style',
        # Цвета
        'color', 'background-color', 'background',
        # Текст
        'text-align', 'text-decoration', 'text-indent', 'text-transform',
        'line-height', 'letter-spacing', 'word-spacing',
        'vertical-align', 'white-space',
        # Размеры
        'width', 'height', 'min-width', 'min-height', 'max-width', 'max-height',
        # Отступы и границы
        'margin', 'margin-top', 'margin-right', 'margin-bottom', 'margin-left',
        'padding', 'padding-top', 'padding-right', 'padding-bottom', 'padding-left',
        'border', 'border-width', 'border-style', 'border-color',
        'border-top', 'border-right', 'border-bottom', 'border-left',
        'border-collapse', 'border-spacing', 'border-radius',
        # Отображение и позиционирование
        'display', 'float', 'clear', 'overflow',
        # Списки
        'list-style', 'list-style-type',
    ]
    
    # CSS Sanitizer для разрешения CSS свойств внутри атрибута style
    css_sanitizer = CSSSanitizer(allowed_css_properties=ALLOWED_CSS_PROPERTIES)
    
    # Очищаем HTML с разрешёнными тегами, атрибутами и CSS свойствами
    cleaned = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        css_sanitizer=css_sanitizer,
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