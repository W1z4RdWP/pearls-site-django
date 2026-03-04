import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, useOutletContext } from 'react-router-dom';
import { fetchMasterDetailContent, fetchLessonDetail } from '../../../api/builder_api';
import KnowledgeBaseSidebar from './KnowledgeBaseSidebar';
import LessonDetailBlock from './LessonDetailBlock';
import './KnowledgeBasePage.css';

const KnowledgeBasePage = () => {
  const { pk } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated } = useOutletContext() || {};
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = pk ? await fetchLessonDetail(Number(pk)) : await fetchMasterDetailContent();
      setData(res);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки базы знаний');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [pk]);

  useEffect(() => {
    if (isAuthenticated) {
      loadData();
    }
  }, [isAuthenticated, loadData]);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/users/login', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  if (!isAuthenticated) {
    return null;
  }

  if (loading && !data) {
    return (
      <div className="kb-page">
        <div className="kb-page__loading" role="status" aria-label="Загрузка">
          <p>Загрузка...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="kb-page">
        <div className="kb-page__error" role="alert">
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const selectedLessonId = data.selected_lesson ? data.selected_lesson.id : null;

  return (
    <div className="kb-page">
      <div className="kb-page__container">
        <KnowledgeBaseSidebar
          categories={data.categories || []}
          uncategorizedLessons={data.uncategorized_lessons || []}
          dictionarySections={data.dictionary_sections || []}
          isReadonly={data.is_readonly}
          selectedLessonId={selectedLessonId}
          urls={data.urls || {}}
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          onCategoriesUpdated={loadData}
        />
        <div className="kb-page__detail" id="detail">
          {data.selected_lesson ? (
            <LessonDetailBlock
              lesson={data.selected_lesson}
              actualizationHistory={data.actualization_history || []}
              actualizationInfo={data.actualization_info}
              today={data.today}
              userIsResponsibleForLesson={data.user_is_responsible_for_lesson}
              pendingDraft={data.pending_draft}
              isReadonly={data.is_readonly}
              isMentorOnly={data.is_mentor_only}
              urls={data.urls || {}}
            />
          ) : (
            <p className="kb-page__empty-detail">Выберите урок для просмотра.</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default KnowledgeBasePage;
