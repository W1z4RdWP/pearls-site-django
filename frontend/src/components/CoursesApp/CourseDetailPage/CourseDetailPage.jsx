import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { fetchCourseDetail, startCourse } from '../../../api/courses_api';
import CourseHero from './CourseHero/CourseHero';
import CourseProgress from './CourseProgress/CourseProgress';
import MaterialsList from './MaterialsList/MaterialsList';
import CourseSidebar from './CourseSidebar/CourseSidebar';
import CompletionModal from './CompletionModal/CompletionModal';
import './CourseDetailPage.css';

const CourseDetailPage = () => {
  const { slug } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCompletion, setShowCompletion] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchCourseDetail(slug);
      setData(result);
      if (result.show_completion_animation) {
        setShowCompletion(true);
      }
    } catch (err) {
      setError(err.message || 'Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    if (data?.course?.title) {
      document.title = data.course.title;
    }
    return () => { document.title = 'Главная'; };
  }, [data?.course?.title]);

  const handleStartCourse = useCallback(async () => {
    try {
      await startCourse(slug);
      await loadData();
    } catch (err) {
      alert(err.message || 'Ошибка при начале курса');
    }
  }, [slug, loadData]);

  if (loading) {
    return (
      <main className="course-detail-page" aria-label="Загрузка курса">
        <div className="container">
          <p className="course-detail-page__loading" aria-live="polite">Загрузка…</p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="course-detail-page" aria-label="Ошибка">
        <div className="container">
          <p className="course-detail-page__error" role="alert">{error}</p>
        </div>
      </main>
    );
  }

  if (!data) return null;

  const {
    course, user_course: userCourse, progress, materials,
    final_quiz: finalQuiz, next_material_link: nextMaterialLink,
    user_trajectories_info: trajectoriesInfo,
    next_course_in_trajectory: nextCourseInTrajectory,
    incident, is_staff: isStaff,
  } = data;

  const isBlocked = userCourse?.status === 'blocked';
  const showContent = !isBlocked && (userCourse || isStaff);

  return (
    <main className="course-detail-page">
      <CourseHero course={course} trajectoriesInfo={trajectoriesInfo} />

      <div className="container">
        {isBlocked && (
          <div className="course-detail-page__blocked" role="alert">
            <i className="fa fa-lock fa-3x" aria-hidden="true" />
            <h2>Курс заблокирован</h2>
            <p>
              Курс не был завершен до установленного срока:{' '}
              <strong>{userCourse.deadline}</strong>
            </p>
            <p>Для разблокировки курса обратитесь в службу поддержки.</p>
          </div>
        )}

        {userCourse && ['started', 'completed'].includes(userCourse.status) && (
          <CourseProgress progress={progress} />
        )}

        {showContent && (
          <div className="course-detail-page__layout">
            <div className="course-detail-page__main">
              <MaterialsList
                materials={materials}
                isStaff={isStaff}
                courseSlug={course.slug}
                userCourseStatus={userCourse?.status}
                hasMaterials={course.has_materials}
                onStartCourse={handleStartCourse}
              />
            </div>
            <div className="course-detail-page__aside">
              <CourseSidebar
                userCourse={userCourse}
                isStaff={isStaff}
                course={course}
                progress={progress}
                finalQuiz={finalQuiz}
                nextMaterialLink={nextMaterialLink}
                nextCourseInTrajectory={nextCourseInTrajectory}
                incident={incident}
              />
            </div>
          </div>
        )}
      </div>

      {showCompletion && (
        <CompletionModal
          trajectoriesInfo={trajectoriesInfo}
          onClose={() => setShowCompletion(false)}
        />
      )}
    </main>
  );
};

export default CourseDetailPage;
