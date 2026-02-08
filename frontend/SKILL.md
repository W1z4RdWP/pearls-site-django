# Frontend React — Методология написания кода

## Структура компонентов

Каждый компонент создаётся в отдельной папке внутри `src/components/`:

```
src/components/
└── ComponentName/
    ├── ComponentName.jsx   # React-компонент
    └── ComponentName.css   # Стили компонента
```

## Правила написания компонентов

### JSX

1. **Один компонент — один файл.** Экспорт по умолчанию (`export default`).
2. **Именование**: PascalCase для компонентов и файлов (`Header.jsx`, `CourseCarousel.jsx`).
3. **Функциональные компоненты** с хуками (`useState`, `useEffect`, `useCallback`).
4. **Props деструктуризация** в параметрах функции:
   ```jsx
   const Card = ({ title, description, icon }) => { ... }
   ```
5. **Условный рендеринг** через `&&` или тернарный оператор:
   ```jsx
   {isAuthenticated && <ProfileMenu />}
   {items.length > 0 ? <List items={items} /> : <Empty />}
   ```
6. **Списки** рендерятся через `.map()` с уникальным `key`.
7. **Обработчики событий** именуются `handleAction` (например `handleClick`, `handleSubmit`).
8. **Константы и статические данные** выносятся за пределы компонента.

### CSS

1. **Один CSS-файл на компонент.** Импортируется в JSX: `import './ComponentName.css'`.
2. **BEM-подобное именование** с префиксом компонента:
   ```css
   .header { }
   .header__logo { }
   .header__nav-link { }
   .header__nav-link--active { }
   ```
3. **CSS-переменные** из `:root` определяются глобально в `index.css` и используются в компонентах.
4. **Адаптивность** через `@media` запросы внутри CSS-файла компонента.
5. **Никаких inline-стилей** в JSX (кроме динамических значений).

### API

1. Все запросы к бэкенду — через единый модуль `src/api/api.js`.
2. **Fetch API** с обработкой ошибок.
3. CSRF-токен передаётся через cookie (Django SessionAuthentication).
4. Базовый URL задаётся через Vite proxy (`/api/` → Django backend).

### Общие правила

- **Не дублировать логику.** Общие утилиты — в `src/utils/`.
- **Не хранить секреты** на клиенте.
- **Семантический HTML**: `<header>`, `<main>`, `<footer>`, `<nav>`, `<section>`.
- **Accessibility**: `aria-label`, `alt` для изображений, семантические роли.
- **Загрузка данных**: `useEffect` + `useState` для API-запросов в компонентах.
- **Обработка состояний загрузки**: показывать loading/error/empty состояния.

### Структура проекта

```
frontend/
├── public/                 # Статические файлы
├── src/
│   ├── api/
│   │   └── api.js          # API-клиент
│   ├── components/
│   │   └── ComponentName/
│   │       ├── ComponentName.jsx
│   │       └── ComponentName.css
│   ├── App.jsx             # Корневой компонент с роутингом
│   ├── App.css             # Стили корневого компонента
│   ├── main.jsx            # Точка входа
│   └── index.css           # Глобальные стили и CSS-переменные
├── index.html              # HTML-шаблон
├── vite.config.js          # Конфигурация Vite
└── package.json
```
