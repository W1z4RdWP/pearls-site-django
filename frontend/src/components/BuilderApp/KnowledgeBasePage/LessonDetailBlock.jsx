import { useState } from 'react';

/** Форматирует ISO-дату (YYYY-MM-DD) в DD.MM.YYYY для отображения */
const formatDate = (iso) => {
  if (!iso) return '—';
  const d = iso.split('T')[0];
  const [y, m, day] = d.split('-');
  return y && m && day ? `${day}.${m}.${y}` : iso;
};

/**
 * Блок детали урока: заголовок, история актуализаций, содержимое, видео, навигация.
 */
const LessonDetailBlock = ({
  lesson,
  actualizationHistory = [],
  actualizationInfo = null,
  today = null,
  userIsResponsibleForLesson = false,
  pendingDraft = null,
  isReadonly,
  isMentorOnly = false,
  urls = {},
}) => {
  const [historyOpen, setHistoryOpen] = useState(false);

  if (!lesson) return null;

  const { id, title, content, video_id: videoId } = lesson;
  const nextUpdate = actualizationInfo?.next_update || null;
  const nextUpdateFormatted = formatDate(nextUpdate);
  const responsibleRole = actualizationInfo?.responsible_role;
  const roleName = responsibleRole?.name ?? '—';
  const isOverdue = today && nextUpdate && nextUpdate < today;

  return (
    <article className="kb-detail" id="lesson-content-block" aria-labelledby="kb-detail-title">
      <header className="kb-detail__header">
        <h2 id="kb-detail-title" className="kb-detail__title">
          {title}
        </h2>
        <div className="kb-detail__header-actions">
          {(isReadonly === false || isMentorOnly) && (
            <div className="kb-detail__actualization">
              <button
                type="button"
                className="kb-detail__history-btn"
                onClick={() => setHistoryOpen((o) => !o)}
                aria-expanded={historyOpen}
                aria-controls="kb-detail-history-panel"
              >
                История актуализаций
              </button>
              {historyOpen && (
                <div
                  id="kb-detail-history-panel"
                  className="kb-detail__history-dropdown"
                  role="region"
                  aria-label="История актуализаций"
                >
                  <div className="kb-detail__history-toolbar">
                    {!isReadonly && userIsResponsibleForLesson && (
                      <a
                        href={`/builder/lesson/${id}/`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="kb-detail__btn kb-detail__btn--primary btn-sm"
                        title="Актуализировать (откроется классическая версия страницы)"
                      >
                        Актуализировать
                      </a>
                    )}
                    {pendingDraft ? (
                      <a href={pendingDraft.edit_url} className="kb-detail__btn kb-detail__btn--info btn-sm">
                        Редактировать черновик
                      </a>
                    ) : (
                      urls.lesson_draft_create && (
                        <a
                          href={urls.lesson_draft_create.replace('{id}', String(id))}
                          className="kb-detail__btn kb-detail__btn--outline btn-sm"
                        >
                          Черновик
                        </a>
                      )
                    )}
                  </div>
                  <div className="kb-detail__history-scroll">
                    <table className="kb-detail__table">
                      <thead>
                        <tr>
                          <th>Дата создания</th>
                          <th>№ версии</th>
                          <th>Стандарт (дней)</th>
                          <th>След. обновление</th>
                          <th>Отв.</th>
                          <th>Отв. ФИО</th>
                        </tr>
                      </thead>
                      <tbody>
                        {actualizationHistory.map((row) => (
                          <tr key={row.version}>
                            <td>{formatDate(row.created_at)}</td>
                            <td className="kb-detail__version-cell">v{row.version}</td>
                            <td>{row.update_period_days ?? '—'}</td>
                            <td className={row.next_update && today && row.next_update < today ? 'kb-detail__cell--overdue' : ''}>
                              {formatDate(row.next_update)}
                            </td>
                            <td>{row.responsible_role?.name ?? '—'}</td>
                            <td>{row.responsible_fio ?? '—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="kb-detail__next-update">
                    <span>След. обновление:</span>
                    <span
                      className={`kb-detail__next-update-value ${isOverdue ? 'kb-detail__next-update-value--overdue' : ''}`}
                    >
                      {nextUpdateFormatted}
                    </span>
                    <span className="kb-detail__responsible">
                      Отв: <strong>{roleName}</strong>
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </header>

      <div
        className="kb-detail__content"
        dangerouslySetInnerHTML={{ __html: content || 'Нет содержимого.' }}
      />

      {videoId && (
        <div className="kb-detail__video">
          <h5>Видео урок:</h5>
          <iframe
            title={`Видео: ${title}`}
            width="560"
            height="315"
            src={`https://rutube.ru/play/embed/${videoId}`}
            frameBorder="0"
            allowFullScreen
          />
        </div>
      )}
    </article>
  );
};

export default LessonDetailBlock;
