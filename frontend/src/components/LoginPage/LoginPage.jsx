import { useEffect } from "react";
import './LoginPage.css';

const LoginPage = () => {
    useEffect(() => {
        document.title = 'Вход в учетную запись';
        return () => {
            document.title = 'Главная';
        };
    }, []);


    return (
        <div className="login-page">
            <div className="login-page__card">
                <h1 className="login-page__title">Вход</h1>
                <form className="login-page__form" action="" method="post">
                    <label className="login-page__field">
                        <span className="login-page__label">Логин</span>
                        <input className="login-page__input" type="text" name="username" placeholder="Введите логин" autoComplete="username" />
                    </label>
                    <label className="login-page__field">
                        <span className="login-page__label">Пароль</span>
                        <input className="login-page__input" type="password" name="password" placeholder="Введите пароль" autoComplete="current-password" />
                    </label>
                    <button className="login-page__btn" type="submit">Войти</button>
                </form>
                <p className="login-page__hint">Нужен аккаунт? Обратитесь к администратору.</p>
            </div>
        </div>
    ) 

}

export default LoginPage;
