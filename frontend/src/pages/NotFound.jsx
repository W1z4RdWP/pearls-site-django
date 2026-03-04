import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import Spinner from 'react-bootstrap/Spinner'; // Если используете react-bootstrap

const NotFound = () => {
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Симуляция задержки загрузки страницы (1.5 секунды)
        const timer = setTimeout(() => {
            setLoading(false);
        }, 1500);

        return () => clearTimeout(timer);
    }, []);

    // if (loading) {
    //     return (
    //         <div className="d-flex justify-content-center align-items-center min-vh-100">
    //             <div className="text-center">
    //                 <Spinner animation="border" variant="primary" role="status" style={{width: '3rem', height: '3rem'}}>
    //                     <span className="visually-hidden">Загрузка...</span>
    //                 </Spinner>
    //                 <p className="mt-3">Загружаем страницу...</p>
    //             </div>
    //         </div>
    //     );
    // }

    return (
        <div className="alert alert-danger text-center">
            <h1>Ошибка 404</h1>
            <p>К сожалению, запрашиваемая страница не найдена.</p>
            <Link to={'/'} className="btn btn-primary">Вернуться на главную</Link>
        </div>
    );
};

export default NotFound;
