import { useState, useEffect, useCallback, useMemo } from 'react';
import { fetchTrajectoryList } from '../../../api/courses_api';
import TrajectoriesSection from './TrajectoriesSection/TrajectoriesSection';
import ProgressStats from './ProgressStats/ProgressStats';
import CourseSearch from './CourseSearch/CourseSearch';
import CoursesGrid from './CoursesGrid/CoursesGrid';
import './UserTrajectoryListPage.css';

/**
 * Фильтрация курсов по поиску, статусу и инцидентам (клиентская).
 */
function filterCourses(coursesData, searchQuery, statusFilter, incidentFilter) {
  if (!coursesData || !coursesData.length) return [];
  let list = [...coursesData];
  const q = (searchQuery || '').trim().toLowerCase();
  if (q) {
    list = list.filter((c) => c.course.title.toLowerCase().includes(q));
  }
  if (statusFilter && statusFilter !== 'all') {
    list = list.filter((c) => c.status === statusFilter);
  }
  if (incidentFilter === 'true') {
    list = list.filter((c) => c.course.is_incident);
  } else if (incidentFilter === 'false') {
    list = list.filter((c) => !c.course.is_incident);
  }
  return list;
}

const UserTrajectoryListPage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('all');
  const [incidentFilter, setIncidentFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchTrajectoryList();
      setData(result);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки данных');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    document.title = 'Траектории и курсы';
    return () => { document.title = 'Главная'; };
  }, []);

  const filteredCourses = useMemo(
    () => filterCourses(data?.courses_data, searchQuery, statusFilter, incidentFilter),
    [data?.courses_data, searchQuery, statusFilter, incidentFilter]
  );

  const hasActiveFilters = searchQuery || incidentFilter !== 'all' || statusFilter !== 'all';

  const handleClearFilters = () => {
    setSearchQuery('');
    setStatusFilter('all');
    setIncidentFilter('all');
  };

  if (loading) {
    return (
      <main className="user-trajectory-list-page" aria-label="Траектории и курсы">
        <div className="user-trajectory-list-page__container">
          <p className="user-trajectory-list-page__loading" aria-live="polite">
            Загрузка…
          </p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="user-trajectory-list-page" aria-label="Траектории и курсы">
        <div className="user-trajectory-list-page__container">
          <p className="user-trajectory-list-page__error" role="alert">
            {error}
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="user-trajectory-list-page" aria-label="Траектории и курсы">
      <div className="user-trajectory-list-page__container container mt-4">
        {data && (
          <>
            <TrajectoriesSection userTrajectories={data.user_trajectories} />

            <section className="user-trajectory-list-page__progress" aria-label="Ваш прогресс по курсам">
              <div className="progress-header">
                <h1 className="progress-title">
                  <i className="fa fa-graduation-cap" aria-hidden="true" /> Ваш прогресс по курсам
                </h1>
                <ProgressStats
                  availableCount={data.available_courses_all}
                  inProgressCount={data.in_progress_courses_all}
                  incidentCount={data.incident_courses_all}
                  completedCount={data.completed_courses_all}
                  statusFilter={statusFilter}
                  incidentFilter={incidentFilter}
                  onStatusFilterChange={setStatusFilter}
                  onIncidentFilterChange={setIncidentFilter}
                  searchQuery={searchQuery}
                />
              </div>

              <CourseSearch
                searchQuery={searchQuery}
                onSearchChange={setSearchQuery}
                onClear={handleClearFilters}
                hasActiveFilters={hasActiveFilters}
              />

              <CoursesGrid coursesData={filteredCourses} statusFilter={statusFilter} />
            </section>
          </>
        )}
      </div>
    </main>
  );
};

export default UserTrajectoryListPage;
