import { useEffect, useState } from "react";
import './AboutPage.css';

const AboutPage = () => {
    const [loading, setLoading] = useState(true);

    // useEffect(() => {
    //     const loadData = async () => {
    //       try {
    //         const data = await fetchAboutPageData();
    //         setData(data || {username: '', first_name: '', user_courses: []});
    //       } catch (err) {
    //         console.error('Ошибка загрузки данных about:', err);
    //       } finally {
    //         setLoading(false);
    //       }
    //     };
    
    //     loadData();
    //   }, []);

    return (
        <div className="about-page">
            <div className="about-page__block">
                <h1>О нас</h1>
                <p>Мы - команда профессионалов, которая занимается обучением персонала клиники "Территория Улыбки".</p>

            </div>
            <div className="about-page__warning-msg">
                <p>❗❗ Данная веб-страница будет постепенно обновляться и наполняться контентом.
                Если у Вас имеются какие-либо идеи или предложения по развитию проекта - прошу обращаться в телеграмм:
                </p>
                <a href="https://t.me/w1z4rdwp">@w1z4rdWP</a>
            </div>

        </div>
    )
}

export default AboutPage;