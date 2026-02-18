import { useState, useCallback, useEffect } from 'react';
import './SearchBox.css';

const SearchBox = ({ initialQuery, onSearch, onReset }) => {
  const [query, setQuery] = useState(initialQuery || '');

  useEffect(() => {
    setQuery(initialQuery || '');
  }, [initialQuery]);

  const handleSubmit = useCallback(
    (e) => {
      e.preventDefault();
      onSearch(query.trim());
    },
    [query, onSearch]
  );

  const handleReset = useCallback(() => {
    setQuery('');
    onReset();
  }, [onReset]);

  return (
    <div className="search-box">
      <form onSubmit={handleSubmit} className="search-box__form">
        <input
          type="text"
          className="search-box__input"
          placeholder="Поиск по имени, фамилии, email или username..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          aria-label="Поиск пользователей"
        />
        <button type="submit" className="search-box__btn search-box__btn--primary">
          <i className="fas fa-search" aria-hidden />
          <span>Найти</span>
        </button>
        {initialQuery && (
          <button
            type="button"
            className="search-box__btn search-box__btn--secondary"
            onClick={handleReset}
            aria-label="Сбросить поиск"
          >
            <i className="fas fa-times" aria-hidden />
            <span>Сбросить</span>
          </button>
        )}
      </form>
    </div>
  );
};

export default SearchBox;
