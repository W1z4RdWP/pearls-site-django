import { useCallback, useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { fetchChangelogData } from "../../api/api";

const ChangeLogPage = () => {
    const { user, isAuthenticated } = useOutletContext();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadChangelog = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetchChangelogData();
            setData(res);
        } catch (err) {
            setError(err.message || 'Ошибка загрузки ченджлога');
            setData(null);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        if(isAuthenticated){
            loadChangelog();
        }
    }, [isAuthenticated, loadChangelog]);




    return(
        <div className="changelog-page">
            <h2>Список изменений</h2>
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
            {!loading && !error && data && (
                <>
                    {data.title}
                </>
            )}
        </div>
    )

}

export default ChangeLogPage;