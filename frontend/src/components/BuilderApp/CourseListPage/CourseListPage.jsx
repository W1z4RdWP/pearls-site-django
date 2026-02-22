import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { fetchCourseList, deleteCourse } from '../../../api/builder_api';
import CourseListStats from './CourseListStats';
import CourseListFilters from './CourseListFilters';
import CourseListItem from './CourseListItem';
import CourseListPagination from './CourseListPagination';
import CourseListEmpty from './CourseListEmpty';
import './CourseListPage.css';


const CourseListPage = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedAuthor, setSelectedAuthor] = useState('');
  const [selectedGroup, setSelectedGroup] = useState('');
  const [page, setPage] = useState(1);
  const [refresh, setRefresh] = useState(0);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deleteSuccess, setDeleteSuccess] = useState(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchCourseList({
        search: searchQuery,
        author: selectedAuthor,
        group: selectedGroup,
        page,
      });
      setData(res);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки данных');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [searchQuery, selectedAuthor, selectedGroup, page, refresh]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleApplyFilters = useCallback(() => {
    setPage(1);
    setRefresh((r) => r + 1);
  }, []);

  const handleAuthorChange = useCallback((value) => {
    setSelectedAuthor(value);
    setPage(1);
  }, []);

  const handleGroupChange = useCallback((value) => {
    setSelectedGroup(value);
    setPage(1);
  }, []);

  const handlePageChange = useCallback((newPage) => {
    setPage(newPage);
  }, []);

  const handleDelete = useCallback(async (slug) => {
    try {
      await deleteCourse(slug);
      setDeleteSuccess('Курс успешно удалён');
      setTimeout(() => setDeleteSuccess(null), 3000);
      loadData();
    } catch (err) {
      window.alert('Ошибка при удалении курса: ' + (err.message || err));
    }
  }, [loadData]);

  if (loading && !data) {
    return (
      <main className="course-list">
        <div className="course-list__loading" role="status" aria-label="Загрузка">
          <p>Загрузка...</p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="course-list">
        <div className="course-list__error" role="alert">
          <p>{error}</p>
        </div>
      </main>
    );
  }

  const items = data?.items ?? [];
  const pagination = data?.pagination;
  const urls = data?.urls ?? {};
  const startIndex = pagination?.start_index ?? 1;

  return (
    <main className="course-list">
      <header className="course-list__header">
        <nav aria-label="breadcrumb">
          <ol className="course-list__breadcrumb">
            <li className="course-list__breadcrumb-item">
              <Link to="/builder/trajectory-management" className="course-list__breadcrumb-link">
                <i className="fas fa-tachometer-alt" aria-hidden /> <span className="course-list__breadcrumb-text--full">Панель управления</span>
              </Link>
            </li>
            <li className="course-list__breadcrumb-item course-list__breadcrumb-item--active" aria-current="page">
              Все курсы
            </li>
          </ol>
        </nav>
        <h1 className="course-list__title">
          <i className="fas fa-graduation-cap course-list__title-icon" aria-hidden /> Все курсы
        </h1>
        <p className="course-list__subtitle">Управление всеми курсами на платформе</p>
      </header>

      {deleteSuccess && (
        <div className="course-list__message course-list__message--success" role="status">
          {deleteSuccess}
        </div>
      )}

      <CourseListStats
        totalCourses={data?.total_courses}
        totalLessons={data?.total_lessons}
        totalAuthors={data?.total_authors}
      />

      <CourseListFilters
        searchQuery={searchQuery}
        selectedAuthor={selectedAuthor}
        selectedGroup={selectedGroup}
        authors={data?.authors}
        groups={data?.groups}
        onSearchChange={setSearchQuery}
        onAuthorChange={handleAuthorChange}
        onGroupChange={handleGroupChange}
        onSubmit={handleApplyFilters}
      />

      <section className="course-list__card">
        <div className="course-list__card-header">
          <h2 className="course-list__card-title">Список курсов</h2>
          <Link to="/courses/create-course" className="course-list__card-create-btn">
            <i className="fas fa-plus" aria-hidden /> Создать курс
          </Link>
        </div>
        <div className="course-list__card-body">
          {items.length > 0 ? (
            <div className="course-list__list">
              {items.map((course, i) => (
                <CourseListItem
                  key={course.id}
                  index={startIndex + i}
                  course={course}
                  urls={urls}
                  onDelete={handleDelete}
                />
              ))}
            </div>
          ) : (
            <CourseListEmpty />
          )}
        </div>
      </section>

      <CourseListPagination pagination={pagination} onPageChange={handlePageChange} />
    </main>
  );
};

export default CourseListPage;
