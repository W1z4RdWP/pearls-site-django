import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  fetchTicketDetail,
  takeTicket,
  closeTicket,
  addTicketComment,
  updateTicket,
  rateTicket,
} from '../../../api/tech_support_api';
import './TicketDetailPage.css';

const RATING_OPTIONS = [
  { value: 1, label: '1 — Очень плохо' },
  { value: 2, label: '2 — Плохо' },
  { value: 3, label: '3 — Удовлетворительно' },
  { value: 4, label: '4 — Хорошо' },
  { value: 5, label: '5 — Отлично' },
];

function getFileType(filename) {
  const fn = (filename || '').toLowerCase();
  if (/\.(jpg|jpeg|png|gif|webp)$/.test(fn)) return 'image';
  if (/\.(mp4|webm|mov)$/.test(fn)) return 'video';
  if (/\.pdf$/.test(fn)) return 'pdf';
  if (/\.(doc|docx)$/.test(fn)) return 'doc';
  if (/\.(txt|log)$/.test(fn)) return 'txt';
  return 'default';
}

const FILE_TYPE_ICONS = {
  image: { className: 'ticket-detail-page__att-icon--img', icon: 'fas fa-image' },
  video: { className: 'ticket-detail-page__att-icon--vid', icon: 'fas fa-play-circle' },
  pdf: { className: 'ticket-detail-page__att-icon--pdf', icon: 'fas fa-file-pdf' },
  doc: { className: 'ticket-detail-page__att-icon--doc', icon: 'fas fa-file-word' },
  txt: { className: 'ticket-detail-page__att-icon--txt', icon: 'fas fa-file-alt' },
  default: { className: 'ticket-detail-page__att-icon--def', icon: 'fas fa-file' },
};

function formatDate(isoStr) {
  if (!isoStr) return '—';
  const d = new Date(isoStr);
  const pad = (n) => String(n).padStart(2, '0');
  return `${pad(d.getDate())}.${pad(d.getMonth() + 1)}.${d.getFullYear()} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function getUserDisplayName(user) {
  if (!user) return '—';
  const full = [user.first_name, user.last_name].filter(Boolean).join(' ');
  return full || user.username;
}

function nl2br(text) {
  if (!text) return '';
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br />');
}

const TicketDetailPage = () => {
  const { ticketId } = useParams();
  const navigate = useNavigate();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

  const [commentText, setCommentText] = useState('');
  const [commentError, setCommentError] = useState(null);

  const [ratingValue, setRatingValue] = useState(5);
  const [ratingFeedback, setRatingFeedback] = useState('');
  const [ratingError, setRatingError] = useState(null);

  const [updateForm, setUpdateForm] = useState({});
  const [updateError, setUpdateError] = useState(null);
  const [updateSuccess, setUpdateSuccess] = useState(false);

  const [lightbox, setLightbox] = useState(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchTicketDetail(Number(ticketId));
      setData(result);
      const t = result.ticket;
      setUpdateForm({
        title: t.title || '',
        status_id: t.status?.id || '',
        priority_id: t.priority?.id || '',
        category_id: t.category?.id || '',
        deadline: t.deadline ? t.deadline.slice(0, 16) : '',
        assigned_to_id: t.assigned_to?.id || '',
      });
    } catch (err) {
      setError(err.message || 'Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  }, [ticketId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    if (data?.ticket?.ticket_number) {
      document.title = `${data.ticket.ticket_number} — ${data.ticket.title}`;
    }
    return () => { document.title = 'Главная'; };
  }, [data?.ticket?.ticket_number, data?.ticket?.title]);

  /* ---- Actions ---- */

  const handleTake = async () => {
    if (actionLoading) return;
    setActionLoading(true);
    try {
      await takeTicket(Number(ticketId));
      await loadData();
    } catch (err) {
      setError(err.message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleClose = async () => {
    if (actionLoading || !window.confirm('Закрыть тикет?')) return;
    setActionLoading(true);
    try {
      await closeTicket(Number(ticketId));
      await loadData();
    } catch (err) {
      setError(err.message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleCommentSubmit = async (e) => {
    e.preventDefault();
    if (!commentText.trim()) return;
    setCommentError(null);
    setActionLoading(true);
    try {
      await addTicketComment(Number(ticketId), commentText.trim());
      setCommentText('');
      await loadData();
    } catch (err) {
      setCommentError(err.message || 'Ошибка отправки комментария');
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpdateSubmit = async (e) => {
    e.preventDefault();
    setUpdateError(null);
    setUpdateSuccess(false);
    setActionLoading(true);
    try {
      const payload = {
        title: updateForm.title,
        status_id: updateForm.status_id ? Number(updateForm.status_id) : null,
        priority_id: updateForm.priority_id ? Number(updateForm.priority_id) : null,
        category_id: updateForm.category_id ? Number(updateForm.category_id) : null,
        deadline: updateForm.deadline || null,
        assigned_to_id: updateForm.assigned_to_id ? Number(updateForm.assigned_to_id) : null,
      };
      await updateTicket(Number(ticketId), payload);
      setUpdateSuccess(true);
      await loadData();
    } catch (err) {
      if (err.errors) {
        setUpdateError(Object.values(err.errors).join(', '));
      } else {
        setUpdateError(err.message || 'Ошибка обновления');
      }
    } finally {
      setActionLoading(false);
    }
  };

  const handleRateSubmit = async (e) => {
    e.preventDefault();
    setRatingError(null);
    setActionLoading(true);
    try {
      await rateTicket(Number(ticketId), Number(ratingValue), ratingFeedback.trim());
      await loadData();
    } catch (err) {
      setRatingError(err.message || 'Ошибка отправки оценки');
    } finally {
      setActionLoading(false);
    }
  };

  /* ---- Lightbox ---- */

  const openLightbox = (url, type) => {
    setLightbox({ url, type });
    document.body.style.overflow = 'hidden';
  };

  const closeLightbox = useCallback((e) => {
    if (e && e.target.tagName === 'VIDEO') return;
    setLightbox(null);
    document.body.style.overflow = '';
  }, []);

  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === 'Escape' && lightbox) closeLightbox(e);
    };
    document.addEventListener('keydown', handleKey);
    return () => document.removeEventListener('keydown', handleKey);
  }, [lightbox, closeLightbox]);

  /* ---- Navigation ---- */

  const handleBackClick = () => {
    if (data?.is_staff_view) {
      navigate('/tech_support/tickets');
    } else {
      navigate('/tech_support/my/tickets');
    }
  };

  /* ---- Loading / Error ---- */

  if (loading && !data) {
    return (
      <main className="ticket-detail-page" aria-label="Загрузка тикета">
        <div className="ticket-detail-page__container">
          <p className="ticket-detail-page__loading" aria-live="polite">Загрузка…</p>
        </div>
      </main>
    );
  }

  if (error && !data) {
    return (
      <main className="ticket-detail-page" aria-label="Ошибка">
        <div className="ticket-detail-page__container">
          <p className="ticket-detail-page__error" role="alert">{error}</p>
          <button type="button" className="ticket-detail-page__btn ticket-detail-page__btn--light" onClick={() => navigate(-1)}>
            Назад
          </button>
        </div>
      </main>
    );
  }

  if (!data) return null;

  const { ticket, comments, attachments, is_staff_view, is_closed, can_comment, can_rate, update_options } = data;

  return (
    <main className="ticket-detail-page">
      <div className="ticket-detail-page__container">

        {/* ===== Header ===== */}
        <div className="ticket-detail-page__header">
          <div className="ticket-detail-page__header-actions">
            {is_staff_view && !is_closed && !ticket.assigned_to && (
              <button type="button" className="ticket-detail-page__btn ticket-detail-page__btn--primary ticket-detail-page__btn--sm" onClick={handleTake} disabled={actionLoading}>
                Взять в работу
              </button>
            )}
            {is_staff_view && !is_closed && (
              <button type="button" className="ticket-detail-page__btn ticket-detail-page__btn--danger ticket-detail-page__btn--sm" onClick={handleClose} disabled={actionLoading}>
                Закрыть тикет
              </button>
            )}
            <button type="button" className="ticket-detail-page__btn ticket-detail-page__btn--light ticket-detail-page__btn--sm" onClick={handleBackClick}>
              <i className="fas fa-arrow-left"></i> Назад к списку
            </button>
          </div>

          <h1 className="ticket-detail-page__ticket-number">
            <i className="fas fa-ticket-alt"></i> {ticket.ticket_number}
          </h1>
          <h2 className="ticket-detail-page__title">{ticket.title}</h2>

          <div className="ticket-detail-page__badges">
            <span className="ticket-detail-page__badge" style={{ backgroundColor: ticket.status?.color || '#6c757d' }}>
              {ticket.status?.name}
            </span>
            <span className="ticket-detail-page__badge" style={{ backgroundColor: ticket.priority?.color || '#6c757d' }}>
              {ticket.priority?.name}
            </span>
            <span className="ticket-detail-page__badge ticket-detail-page__badge--secondary">
              {ticket.ticket_type_display}
            </span>
          </div>
        </div>

        {/* ===== Overdue warning ===== */}
        {ticket.is_overdue && (
          <div className="ticket-detail-page__overdue" role="alert">
            <i className="fas fa-exclamation-triangle ticket-detail-page__overdue-icon"></i>
            <div>
              <strong>Тикет просрочен!</strong>
              <p className="ticket-detail-page__overdue-text">Дедлайн: {formatDate(ticket.deadline)}</p>
            </div>
          </div>
        )}

        {/* ===== Two-column layout ===== */}
        <div className="ticket-detail-page__layout">

          {/* --- Main column --- */}
          <div className="ticket-detail-page__main">

            {/* Description */}
            <section className="ticket-detail-page__card">
              <h4 className="ticket-detail-page__card-title">
                <i className="fas fa-info-circle"></i> Описание проблемы
              </h4>
              <div
                className="ticket-detail-page__description"
                dangerouslySetInnerHTML={{ __html: nl2br(ticket.description) }}
              />

              <div className="ticket-detail-page__meta-grid">
                <div className="ticket-detail-page__meta-item">
                  <h6><i className="fas fa-user"></i> Создатель</h6>
                  <p>
                    <Link to={`/user_management/users/${ticket.created_by?.id}/edit`}>
                      {getUserDisplayName(ticket.created_by)}
                    </Link>
                    <br />
                    <small className="ticket-detail-page__text-muted">{ticket.created_by?.email}</small>
                  </p>
                </div>
                <div className="ticket-detail-page__meta-item">
                  <h6><i className="fas fa-calendar"></i> Дата создания</h6>
                  <p>{formatDate(ticket.created_at)}</p>
                </div>
              </div>

              {ticket.assigned_to && (
                <div className="ticket-detail-page__meta-grid">
                  <div className="ticket-detail-page__meta-item">
                    <h6><i className="fas fa-user-tie"></i> Исполнитель</h6>
                    <p>
                      {getUserDisplayName(ticket.assigned_to)}
                      <br />
                      <small className="ticket-detail-page__text-muted">{ticket.assigned_to?.email}</small>
                    </p>
                  </div>
                  <div className="ticket-detail-page__meta-item">
                    <h6><i className="fas fa-clock"></i> Дедлайн</h6>
                    <p>
                      {formatDate(ticket.deadline)}
                      {ticket.deadline_hours_left != null && (
                        <>
                          <br />
                          <small className="ticket-detail-page__text-muted">
                            {ticket.is_overdue
                              ? `Просрочен на ${Math.round(ticket.deadline_hours_left)} ч.`
                              : `Осталось ${Math.round(ticket.deadline_hours_left)} ч.`}
                          </small>
                        </>
                      )}
                    </p>
                  </div>
                </div>
              )}
            </section>

            {/* Attachments */}
            {attachments.length > 0 && (
              <section className="ticket-detail-page__card">
                <h4 className="ticket-detail-page__card-title">
                  <i className="fas fa-paperclip"></i> Вложения
                  <span className="ticket-detail-page__count-badge">{attachments.length}</span>
                </h4>
                <div className="ticket-detail-page__attachments-grid">
                  {attachments.map((att) => {
                    const fileType = getFileType(att.filename);
                    const iconInfo = FILE_TYPE_ICONS[fileType];
                    return (
                      <div className="ticket-detail-page__att-card" key={att.id}>
                        {fileType === 'image' ? (
                          <img
                            src={att.file_url}
                            alt={att.filename}
                            className="ticket-detail-page__att-thumb"
                            onClick={() => openLightbox(att.file_url, 'image')}
                          />
                        ) : (
                          <div
                            className={`ticket-detail-page__att-icon ${iconInfo.className}`}
                            onClick={fileType === 'video' ? () => openLightbox(att.file_url, 'video') : undefined}
                            role={fileType === 'video' ? 'button' : undefined}
                            tabIndex={fileType === 'video' ? 0 : undefined}
                          >
                            <i className={iconInfo.icon}></i>
                          </div>
                        )}
                        <div className="ticket-detail-page__att-meta">
                          <div className="ticket-detail-page__att-name">{att.filename}</div>
                          <div className="ticket-detail-page__att-date">
                            <i className="far fa-clock"></i> {formatDate(att.uploaded_at)}
                          </div>
                        </div>
                        <a
                          href={att.file_url}
                          className="ticket-detail-page__btn ticket-detail-page__btn--outline ticket-detail-page__btn--sm"
                          download
                          title="Скачать"
                        >
                          <i className="fas fa-download"></i>
                        </a>
                      </div>
                    );
                  })}
                </div>
              </section>
            )}

            {/* Comments */}
            <section className="ticket-detail-page__card">
              <h4 className="ticket-detail-page__card-title">
                <i className="fas fa-comments"></i> Комментарии
              </h4>

              {comments.length > 0 ? (
                comments.map((c) => (
                  <div
                    className={`ticket-detail-page__comment${c.is_internal ? ' ticket-detail-page__comment--internal' : ''}`}
                    key={c.id}
                  >
                    <div className="ticket-detail-page__comment-header">
                      <span className="ticket-detail-page__comment-author">
                        {getUserDisplayName(c.author)}
                        {c.is_internal && (
                          <span className="ticket-detail-page__badge ticket-detail-page__badge--danger ticket-detail-page__badge--sm">
                            Внутренний
                          </span>
                        )}
                      </span>
                      <span className="ticket-detail-page__comment-time">{formatDate(c.created_at)}</span>
                    </div>
                    <div
                      className="ticket-detail-page__comment-content"
                      dangerouslySetInnerHTML={{ __html: nl2br(c.content) }}
                    />
                  </div>
                ))
              ) : (
                <p className="ticket-detail-page__text-muted">Пока нет комментариев</p>
              )}

              <hr className="ticket-detail-page__divider" />
              <h5 className="ticket-detail-page__subtitle">Добавить комментарий</h5>

              {can_comment ? (
                <form onSubmit={handleCommentSubmit}>
                  <textarea
                    className="ticket-detail-page__textarea"
                    rows={3}
                    placeholder="Ответ пользователю..."
                    value={commentText}
                    onChange={(e) => setCommentText(e.target.value)}
                    aria-label="Текст комментария"
                  />
                  {commentError && <p className="ticket-detail-page__form-error">{commentError}</p>}
                  <button
                    type="submit"
                    className="ticket-detail-page__btn ticket-detail-page__btn--primary"
                    disabled={actionLoading || !commentText.trim()}
                  >
                    <i className="fas fa-paper-plane"></i> Отправить комментарий
                  </button>
                </form>
              ) : (
                <p className="ticket-detail-page__text-muted">Тикет закрыт. Комментирование недоступно.</p>
              )}
            </section>
          </div>

          {/* --- Sidebar --- */}
          <aside className="ticket-detail-page__sidebar">

            {/* Staff update form */}
            {is_staff_view && update_options && (
              <section className="ticket-detail-page__card">
                <h5 className="ticket-detail-page__card-title">Параметры тикета</h5>
                <form onSubmit={handleUpdateSubmit}>
                  <div className="ticket-detail-page__form-group">
                    <label className="ticket-detail-page__label">Заголовок</label>
                    <input
                      type="text"
                      className="ticket-detail-page__input"
                      value={updateForm.title}
                      onChange={(e) => setUpdateForm((f) => ({ ...f, title: e.target.value }))}
                    />
                  </div>
                  <div className="ticket-detail-page__form-row">
                    <div className="ticket-detail-page__form-group">
                      <label className="ticket-detail-page__label">Статус</label>
                      <select
                        className="ticket-detail-page__select"
                        value={updateForm.status_id}
                        onChange={(e) => setUpdateForm((f) => ({ ...f, status_id: e.target.value }))}
                      >
                        {update_options.statuses.map((s) => (
                          <option key={s.id} value={s.id}>{s.name}</option>
                        ))}
                      </select>
                    </div>
                    <div className="ticket-detail-page__form-group">
                      <label className="ticket-detail-page__label">Приоритет</label>
                      <select
                        className="ticket-detail-page__select"
                        value={updateForm.priority_id}
                        onChange={(e) => setUpdateForm((f) => ({ ...f, priority_id: e.target.value }))}
                      >
                        {update_options.priorities.map((p) => (
                          <option key={p.id} value={p.id}>{p.name}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                  <div className="ticket-detail-page__form-row">
                    <div className="ticket-detail-page__form-group">
                      <label className="ticket-detail-page__label">Категория</label>
                      <select
                        className="ticket-detail-page__select"
                        value={updateForm.category_id}
                        onChange={(e) => setUpdateForm((f) => ({ ...f, category_id: e.target.value }))}
                      >
                        {update_options.categories.map((c) => (
                          <option key={c.id} value={c.id}>{c.name}</option>
                        ))}
                      </select>
                    </div>
                    <div className="ticket-detail-page__form-group">
                      <label className="ticket-detail-page__label">Дедлайн</label>
                      <input
                        type="datetime-local"
                        className="ticket-detail-page__input"
                        value={updateForm.deadline}
                        onChange={(e) => setUpdateForm((f) => ({ ...f, deadline: e.target.value }))}
                      />
                    </div>
                  </div>
                  <div className="ticket-detail-page__form-group">
                    <label className="ticket-detail-page__label">Ответственный</label>
                    <select
                      className="ticket-detail-page__select"
                      value={updateForm.assigned_to_id}
                      onChange={(e) => setUpdateForm((f) => ({ ...f, assigned_to_id: e.target.value }))}
                    >
                      <option value="">— Не назначен —</option>
                      {update_options.staff_users.map((u) => (
                        <option key={u.id} value={u.id}>{u.display_name}</option>
                      ))}
                    </select>
                  </div>
                  {updateError && <p className="ticket-detail-page__form-error">{updateError}</p>}
                  {updateSuccess && <p className="ticket-detail-page__form-success">Сохранено</p>}
                  <button
                    type="submit"
                    className="ticket-detail-page__btn ticket-detail-page__btn--outline"
                    disabled={actionLoading}
                  >
                    Сохранить
                  </button>
                </form>
              </section>
            )}

            {/* Rating form */}
            {can_rate && (
              <section className="ticket-detail-page__card">
                <h5 className="ticket-detail-page__card-title">
                  <i className="fas fa-star"></i> Оценить решение
                </h5>
                <form onSubmit={handleRateSubmit}>
                  <div className="ticket-detail-page__form-group">
                    <label className="ticket-detail-page__label">Оценка</label>
                    <select
                      className="ticket-detail-page__select"
                      value={ratingValue}
                      onChange={(e) => setRatingValue(e.target.value)}
                    >
                      {RATING_OPTIONS.map((o) => (
                        <option key={o.value} value={o.value}>{o.label}</option>
                      ))}
                    </select>
                  </div>
                  <div className="ticket-detail-page__form-group">
                    <label className="ticket-detail-page__label">Отзыв</label>
                    <textarea
                      className="ticket-detail-page__textarea"
                      rows={3}
                      placeholder="Ваш отзыв о решении проблемы..."
                      value={ratingFeedback}
                      onChange={(e) => setRatingFeedback(e.target.value)}
                    />
                  </div>
                  {ratingError && <p className="ticket-detail-page__form-error">{ratingError}</p>}
                  <button
                    type="submit"
                    className="ticket-detail-page__btn ticket-detail-page__btn--success"
                    disabled={actionLoading}
                  >
                    <i className="fas fa-star"></i> Отправить оценку
                  </button>
                </form>
              </section>
            )}

            {/* Existing rating display */}
            {ticket.rating && (
              <section className="ticket-detail-page__card">
                <h5 className="ticket-detail-page__card-title">
                  <i className="fas fa-star"></i> Оценка
                </h5>
                <div className="ticket-detail-page__rating-stars">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <i key={i} className={i <= ticket.rating ? 'fas fa-star' : 'far fa-star'}></i>
                  ))}
                  <span className="ticket-detail-page__text-muted"> ({ticket.rating}/5)</span>
                </div>
                {ticket.student_feedback && (
                  <p className="ticket-detail-page__feedback">
                    <em>&laquo;{ticket.student_feedback}&raquo;</em>
                  </p>
                )}
              </section>
            )}
          </aside>
        </div>
      </div>

      {/* ===== Lightbox ===== */}
      {lightbox && (
        <div className="ticket-detail-page__lightbox" onClick={closeLightbox} role="dialog" aria-modal="true">
          <button className="ticket-detail-page__lightbox-close" onClick={closeLightbox} aria-label="Закрыть">
            &times;
          </button>
          {lightbox.type === 'video' ? (
            <video src={lightbox.url} controls autoPlay className="ticket-detail-page__lightbox-media" />
          ) : (
            <img src={lightbox.url} alt="" className="ticket-detail-page__lightbox-media" />
          )}
        </div>
      )}
    </main>
  );
};

export default TicketDetailPage;
