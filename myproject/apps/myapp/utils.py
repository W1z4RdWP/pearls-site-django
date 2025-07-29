import bleach

def clean_rutube_iframe(html: str) -> str:
    def rutube_only(tag, name, value):
        # Разрешаем только src, frameborder, allow, allowfullscreen, width, height для iframe
        if tag == 'iframe':
            if name in ['src', 'frameborder', 'allow', 'allowfullscreen', 'width', 'height']:
                # src должен быть только rutube
                if name == 'src' and not value.startswith('https://rutube.ru/play/embed/'):
                    return False
                return True
        return False

    return bleach.clean(
        html,
        tags=['iframe'],
        attributes=rutube_only,
        strip=True
    )