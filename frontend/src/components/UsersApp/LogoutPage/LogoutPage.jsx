import { useEffect } from "react";
import { useNavigate, useOutletContext } from "react-router-dom";
import { logoutUser } from '../../../api/api';

const LogoutPage = () => {
    const navigate = useNavigate();
    const { isAuthenticated, refreshLayout } = useOutletContext();

    useEffect(() => {
        document.title = 'Досвидания!';
        return () => {
          document.title = 'Главная';
        };
      }, []);

    useEffect(() => {
        if(!isAuthenticated){
            navigate('/users/login', {replace: true});
        }
    }, [isAuthenticated, navigate]);



    return (
        <div className="logout-page">
            <div className="logout-page__card">
                <h1 className="logout-page__title">
                    Досвидания!
                </h1>
            </div>
        </div>
    )
}

export default LogoutPage;