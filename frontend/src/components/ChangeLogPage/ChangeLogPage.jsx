import { useCallback, useEffect, useState } from "react";
import { useOutletContext, useSearchParams } from "react-router-dom";
import { fetchChangelogList } from "../../api/myapp_api";
import './ChangeLogPage.css';

const ChangeLogPage = () => {
    const { user, isAuthenticated } = useOutletContext();
    const [searchParams, setSearchParams] = useSearchParams();
    const [items, setItems] = useState([]);
    const [pagination, setPagination] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const currentPage = parseInt(searchParams.get('page') || '1', 10);

    const loadChangelog = useCallback(async (page = 1) => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetchChangelogList(page);
            setItems(res.items || []);
            setPagination(res.pagination || null);
        } catch (err) {
            setError(err.message || 'Ошибка загрузки истории изменений');
            setItems([]);
            setPagination(null);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadChangelog(currentPage);
    }, [currentPage, loadChangelog]);

    const handlePageChange = (page) => {
        setSearchParams({ page: page.toString() });
    };

    const formatDescription = (text) => {
        return text.split('\n').map((line, index) => (
            <span key={index}>
                {line}
                {index < text.split('\n').length - 1 && <br />}
            </span>
        ));
    };

    return (
        <div className="changelog-page">
            <div className="container py-5">
                <h1 className="mb-4">История изменений</h1>
                
                {pagination && (
                    <div className="pagination">
                        <span className="step-links">
                            {pagination.has_previous && (
                                <>
                                    <button 
                                        onClick={() => handlePageChange(1)}
                                        className="pagination-link"
                                    >
                                        &laquo; Первая страница
                                    </button>
                                    <button 
                                        onClick={() => handlePageChange(pagination.previous_page_number)}
                                        className="pagination-link"
                                    >
                                        Предыдущая
                                    </button>
                                </>
                            )}

                            <span className="current">
                                Страница {pagination.page} из {pagination.num_pages}.
                            </span>

                            {pagination.has_next && (
                                <>
                                    <button 
                                        onClick={() => handlePageChange(pagination.next_page_number)}
                                        className="pagination-link"
                                    >
                                        Следующая
                                    </button>
                                    <button 
                                        onClick={() => handlePageChange(pagination.num_pages)}
                                        className="pagination-link"
                                    >
                                        Последняя страница &raquo;
                                    </button>
                                </>
                            )}
                        </span>
                    </div>
                )}

                {loading && (
                    <div className="changelog-page__loading">
                        <p>Загрузка...</p>
                    </div>
                )}

                {error && (
                    <div className="changelog-page__error" role="alert">
                        <p>{error}</p>
                    </div>
                )}

                {!loading && !error && items.length > 0 && (
                    <div className="timeline">
                        {items.map((change, index) => (
                            <div 
                                key={change.id} 
                                className={`timeline-card ${index % 2 === 0 ? 'left' : 'right'}`}
                            >
                                <div className={`card shadow-sm ${change.type}`}>
                                    <div className="card-header">
                                        <div className="version-badge">
                                            <span className="version">Версия {change.version}</span>
                                            <span className="date">{change.release_date}</span>
                                        </div>
                                        <span className="type-badge">{change.type_display}</span>
                                    </div>
                                    <div className="card-body">
                                        <h5 className="card-title">{change.title}</h5>
                                        <div className="card-text">
                                            {formatDescription(change.description)}
                                        </div>
                                        {change.related_link && (
                                            <a 
                                                href={change.related_link}
                                                className="btn btn-outline-primary mt-3"
                                                style={{ width: '120px' }}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                            >
                                                Подробнее
                                            </a>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {!loading && !error && items.length === 0 && (
                    <div className="changelog-page__empty">
                        <p>Записи отсутствуют</p>
                    </div>
                )}

                {pagination && (
                    <div className="pagination">
                        <span className="step-links">
                            {pagination.has_previous && (
                                <>
                                    <button 
                                        onClick={() => handlePageChange(1)}
                                        className="pagination-link"
                                    >
                                        &laquo; Первая страница
                                    </button>
                                    <button 
                                        onClick={() => handlePageChange(pagination.previous_page_number)}
                                        className="pagination-link"
                                    >
                                        Предыдущая
                                    </button>
                                </>
                            )}

                            <span className="current">
                                Страница {pagination.page} из {pagination.num_pages}.
                            </span>

                            {pagination.has_next && (
                                <>
                                    <button 
                                        onClick={() => handlePageChange(pagination.next_page_number)}
                                        className="pagination-link"
                                    >
                                        Следующая
                                    </button>
                                    <button 
                                        onClick={() => handlePageChange(pagination.num_pages)}
                                        className="pagination-link"
                                    >
                                        Последняя страница &raquo;
                                    </button>
                                </>
                            )}
                        </span>
                    </div>
                )}
            </div>
        </div>
    );
}

export default ChangeLogPage;