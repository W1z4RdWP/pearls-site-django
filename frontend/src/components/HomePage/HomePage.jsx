import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import HeroSection from '../HeroSection/HeroSection';
import StaffCarousel from '../StaffCarousel/StaffCarousel';
import FeatureCards from '../FeatureCards/FeatureCards';
import CourseCarousel from '../CourseCarousel/CourseCarousel';
import { fetchHomeCourses } from '../../api/api';
import './HomePage.css';

const HomePage = () => {
  const { isAuthenticated } = useOutletContext();
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadCourses = async () => {
      try {
        const data = await fetchHomeCourses();
        setCourses(data.courses || []);
      } catch (err) {
        console.error('Ошибка загрузки курсов:', err);
      } finally {
        setLoading(false);
      }
    };

    loadCourses();
  }, []);

  return (
    <div className="home-page">
      <HeroSection isAuthenticated={isAuthenticated} />
      <StaffCarousel />
      <FeatureCards />

      {loading ? (
        <div className="home-page__loading">
          <div className="home-page__spinner" />
          <p>Загрузка курсов...</p>
        </div>
      ) : (
        <CourseCarousel courses={courses} />
      )}
    </div>
  );
};

export default HomePage;
