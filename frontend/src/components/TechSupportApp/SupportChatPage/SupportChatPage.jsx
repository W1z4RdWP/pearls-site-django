import { useState, useCallback } from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import { createTicket } from '../../../api/tech_support_api';
import './SupportChatPage.css';

const TICKET_TYPES = [
  { value: 'academic', label: 'Учебные вопросы', desc: 'Расписание, доступ к курсам/урокам и т.п.', icon: 'fa-graduation-cap', iconClass: 'support-chat__type-icon--primary' },
  { value: 'technical', label: 'Технические проблемы', desc: 'Ошибки сайта, ПО, интернет', icon: 'fa-bug', iconClass: 'support-chat__type-icon--danger' },
  { value: 'administrative', label: 'Административные запросы', desc: 'Документы, сертификаты, оплаты', icon: 'fa-file-signature', iconClass: 'support-chat__type-icon--warning' },
  { value: 'suggestions', label: 'Предложения/замечания', desc: 'Идеи по улучшению', icon: 'fa-lightbulb', iconClass: 'support-chat__type-icon--success' },
  { value: 'consultation', label: 'Запрос на консультацию', desc: 'Консультация с преподавателем', icon: 'fa-chalkboard-teacher', iconClass: 'support-chat__type-icon--info' },
];

const TYPE_CONFIG = {
  academic: {
    stepTitle: 'Шаг 2. Учебные вопросы',
    titleLabel: 'Заголовок',
    titleHelp: 'Например: «У меня остались вопросы по уроку №2. Помогите, пожалуйста, разобраться.»',
    descLabel: 'Описание вопроса/проблемы',
    descHelp: 'Курс, номер урока, что именно не получается',
    extra: null,
  },
  technical: {
    stepTitle: 'Шаг 2. Техническая проблема',
    titleLabel: 'Краткое описание неисправности',
    titleHelp: 'Например: «Ошибка 500 при открытии профиля»',
    descLabel: 'Подробное описание неисправности',
    descHelp: 'Что делали до ошибки, что ожидали, браузер/ОС',
    extra: 'repro',
  },
  administrative: {
    stepTitle: 'Шаг 2. Административный запрос',
    titleLabel: 'Тема запроса',
    titleHelp: 'Например: «Нужна справка об обучении»',
    descLabel: 'Описание запроса',
    descHelp: 'Какие документы/данные нужны и к какому курсу',
    extra: null,
  },
  suggestions: {
    stepTitle: 'Шаг 2. Предложения и замечания',
    titleLabel: 'Коротко о предложении/замечании',
    titleHelp: 'Например: «Улучшить поиск по курсам»',
    descLabel: 'Подробности',
    descHelp: 'Что именно улучшить и зачем',
    extra: null,
  },
  consultation: {
    stepTitle: 'Шаг 2. Запрос на консультацию',
    titleLabel: 'Тема консультации',
    titleHelp: 'Например: «Вопрос по ДЗ модуля 2»',
    descLabel: 'Комментарий для преподавателя',
    descHelp: 'Кратко опишите вопрос',
    extra: 'consultation',
  },
};

function SupportChatPage() {
  const { user } = useOutletContext() || {};
  const navigate = useNavigate();
  const isStaff = user?.is_staff || user?.is_superuser;

  const [step, setStep] = useState(1);
  const [ticketType, setTicketType] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [extraRepro, setExtraRepro] = useState('');
  const [extraTeacher, setExtraTeacher] = useState('');
  const [extraDatetime, setExtraDatetime] = useState('');
  const [extraFormat, setExtraFormat] = useState('Онлайн');

  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [nonFieldError, setNonFieldError] = useState('');

  const config = ticketType ? (TYPE_CONFIG[ticketType] || TYPE_CONFIG.academic) : null;

  const handleSelectType = useCallback((value) => {
    setTicketType(value);
    setErrors({});
  }, []);

  const handleToStep2 = useCallback(() => {
    if (!ticketType) return;
    setStep(2);
    setErrors({});
  }, [ticketType]);

  const handleBackToStep1 = useCallback(() => {
    setStep(1);
    setErrors({});
    setNonFieldError('');
  }, []);

  const buildDescription = useCallback(() => {
    let text = description.trim();
    if (ticketType === 'consultation') {
      const parts = [];
      if (extraTeacher.trim()) parts.push(`Преподаватель: ${extraTeacher.trim()}`);
      if (extraDatetime.trim()) parts.push(`Желаемые дата/время: ${extraDatetime.trim()}`);
      if (extraFormat.trim()) parts.push(`Формат: ${extraFormat.trim()}`);
      if (parts.length) text += `\n\n${parts.join('\n')}`;
    }
    if (ticketType === 'technical' && extraRepro.trim()) {
      text += `\n\nШаги воспроизведения:\n${extraRepro.trim()}`;
    }
    return text;
  }, [description, ticketType, extraTeacher, extraDatetime, extraFormat, extraRepro]);

  const handleSubmit = useCallback(
    async (e) => {
      e.preventDefault();
      setNonFieldError('');
      setErrors({});

      const fullDescription = buildDescription();
      if (fullDescription.length < 10) {
        setErrors((prev) => ({ ...prev, description: ['Опишите проблему чуть подробнее (минимум 10 символов).'] }));
        return;
      }
      if (title.trim().length < 5) {
        setErrors((prev) => ({ ...prev, title: ['Заголовок слишком короткий (минимум 5 символов).'] }));
        return;
      }

      setSubmitting(true);
      try {
        const data = await createTicket({
          ticket_type: ticketType,
          title: title.trim(),
          description: fullDescription,
        });
        if (data.ticket_detail_url) {
          window.location.href = data.ticket_detail_url;
        } else {
          navigate(`/tech_support/ticket/${data.ticket_id}/`);
        }
      } catch (err) {
        if (err.errors) {
          setErrors(err.errors);
        } else {
          setNonFieldError(err.message || 'Не удалось отправить обращение.');
        }
      } finally {
        setSubmitting(false);
      }
    },
    [ticketType, title, buildDescription, navigate]
  );

  return (
    <div className="support-chat">
      <div className="support-chat__container">
        <div className="support-chat__header">
          <h1 className="support-chat__title">
            <i className="fas fa-life-ring support-chat__title-icon" aria-hidden />
            Обращение в поддержку
          </h1>
          <div className="support-chat__actions">
            {isStaff && (
              <a href="/tech_support/dashboard/" className="support-chat__btn support-chat__btn--outline">
                <i className="fas fa-tachometer-alt" aria-hidden /> Дашборд
              </a>
            )}
            <a href={isStaff ? "/tech_support/tickets" : "/tech_support/my/tickets"} className="support-chat__btn support-chat__btn--secondary">
              <i className="fas fa-ticket-alt" aria-hidden /> {isStaff ? 'Список тикетов' : 'Мои тикеты'}
            </a>
          </div>
        </div>

        <div className="support-chat__alert support-chat__alert--info" role="status">
          Опишите суть проблемы как можно конкретнее. После отправки вам откроется созданный тикет.
        </div>

        <div className="support-chat__card">
          <div className="support-chat__stepper" aria-label="Шаги формы">
            <div className={`support-chat__step ${step >= 1 ? 'support-chat__step--active' : ''}`} aria-current={step === 1 ? 'step' : undefined}>
              1
            </div>
            <div className={`support-chat__step-line ${step >= 2 ? 'support-chat__step-line--active' : ''}`} />
            <div className={`support-chat__step ${step >= 2 ? 'support-chat__step--active' : ''}`} aria-current={step === 2 ? 'step' : undefined}>
              2
            </div>
          </div>

          <form onSubmit={handleSubmit} className="support-chat__form" noValidate>
            {nonFieldError && (
              <div className="support-chat__alert support-chat__alert--danger" role="alert">
                {nonFieldError}
              </div>
            )}

            {step === 1 && (
              <section className="support-chat__step-section support-chat__step-section--active" aria-labelledby="step1-heading">
                <h2 id="step1-heading" className="support-chat__step-heading">
                  Шаг 1. Выберите тип обращения
                </h2>
                <div className="support-chat__types">
                  {TICKET_TYPES.map((t) => (
                    <div
                      key={t.value}
                      role="button"
                      tabIndex={0}
                      className={`support-chat__type-card ${ticketType === t.value ? 'support-chat__type-card--selected' : ''}`}
                      onClick={() => handleSelectType(t.value)}
                      onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && handleSelectType(t.value)}
                      data-type-value={t.value}
                      aria-pressed={ticketType === t.value}
                      aria-label={`${t.label}: ${t.desc}`}
                    >
                      <div className="support-chat__type-inner">
                        <i className={`fas ${t.icon} support-chat__type-icon ${t.iconClass}`} aria-hidden />
                        <div>
                          <div className="support-chat__type-label">{t.label}</div>
                          <div className="support-chat__type-desc">{t.desc}</div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="support-chat__step-actions">
                  <button
                    type="button"
                    className="support-chat__btn support-chat__btn--primary"
                    onClick={handleToStep2}
                    disabled={!ticketType}
                  >
                    Далее <i className="fas fa-arrow-right support-chat__btn-icon" aria-hidden />
                  </button>
                </div>
              </section>
            )}

            {step === 2 && config && (
              <section className="support-chat__step-section support-chat__step-section--active" aria-labelledby="step2-heading">
                <div className="support-chat__step2-header">
                  <h2 id="step2-heading" className="support-chat__step-heading support-chat__step-heading--mb0">
                    {config.stepTitle}
                  </h2>
                  <button type="button" className="support-chat__btn support-chat__btn--outline" onClick={handleBackToStep1}>
                    <i className="fas fa-arrow-left" aria-hidden /> Назад
                  </button>
                </div>

                <div className="support-chat__fields">
                  <div className="support-chat__field support-chat__field--wide">
                    <label htmlFor="support-chat-title" className="support-chat__label">
                      {config.titleLabel}
                    </label>
                    <input
                      id="support-chat-title"
                      type="text"
                      className="support-chat__input"
                      placeholder="Коротко опишите проблему"
                      value={title}
                      onChange={(e) => setTitle(e.target.value)}
                      aria-invalid={!!errors.title}
                      aria-describedby={errors.title ? 'support-chat-title-error' : 'support-chat-title-help'}
                    />
                    {errors.title && (
                      <div id="support-chat-title-error" className="support-chat__error" role="alert">
                        {errors.title[0]}
                      </div>
                    )}
                    {!errors.title && (
                      <div id="support-chat-title-help" className="support-chat__help">{config.titleHelp}</div>
                    )}
                  </div>

                  <div className="support-chat__field support-chat__field--full">
                    <label htmlFor="support-chat-description" className="support-chat__label">
                      {config.descLabel}
                    </label>
                    <textarea
                      id="support-chat-description"
                      className="support-chat__textarea"
                      rows={6}
                      placeholder="Подробно опишите проблему, шаги воспроизведения, ожидаемый результат и т.п."
                      value={description}
                      onChange={(e) => setDescription(e.target.value)}
                      aria-invalid={!!errors.description}
                      aria-describedby={errors.description ? 'support-chat-desc-error' : 'support-chat-desc-help'}
                    />
                    {errors.description && (
                      <div id="support-chat-desc-error" className="support-chat__error" role="alert">
                        {errors.description[0]}
                      </div>
                    )}
                    {!errors.description && (
                      <div id="support-chat-desc-help" className="support-chat__help">{config.descHelp}</div>
                    )}
                  </div>

                  {config.extra === 'repro' && (
                    <div className="support-chat__field support-chat__field--full">
                      <label htmlFor="support-chat-repro" className="support-chat__label">
                        Шаги воспроизведения (опционально)
                      </label>
                      <textarea
                        id="support-chat-repro"
                        className="support-chat__textarea"
                        rows={3}
                        placeholder="1) ... 2) ... 3) ..."
                        value={extraRepro}
                        onChange={(e) => setExtraRepro(e.target.value)}
                      />
                    </div>
                  )}

                  {config.extra === 'consultation' && (
                    <div className="support-chat__extra-fields">
                      <div className="support-chat__field">
                        <label htmlFor="support-chat-teacher" className="support-chat__label">
                          Преподаватель (ФИО, если известно)
                        </label>
                        <input
                          id="support-chat-teacher"
                          type="text"
                          className="support-chat__input"
                          placeholder="Иванов И.И."
                          value={extraTeacher}
                          onChange={(e) => setExtraTeacher(e.target.value)}
                        />
                      </div>
                      <div className="support-chat__field">
                        <label htmlFor="support-chat-datetime" className="support-chat__label">
                          Желаемые дата и время
                        </label>
                        <input
                          id="support-chat-datetime"
                          type="datetime-local"
                          className="support-chat__input"
                          value={extraDatetime}
                          onChange={(e) => setExtraDatetime(e.target.value)}
                        />
                      </div>
                      <div className="support-chat__field">
                        <label htmlFor="support-chat-format" className="support-chat__label">
                          Формат
                        </label>
                        <select
                          id="support-chat-format"
                          className="support-chat__select"
                          value={extraFormat}
                          onChange={(e) => setExtraFormat(e.target.value)}
                        >
                          <option value="Онлайн">Онлайн</option>
                          <option value="Оффлайн">Оффлайн</option>
                        </select>
                      </div>
                    </div>
                  )}
                </div>

                <div className="support-chat__step-actions">
                  <button type="submit" className="support-chat__btn support-chat__btn--primary" disabled={submitting}>
                    {submitting ? (
                      'Отправка...'
                    ) : (
                      <>
                        <i className="fas fa-paper-plane support-chat__btn-icon" aria-hidden /> Отправить обращение
                      </>
                    )}
                  </button>
                </div>
              </section>
            )}
          </form>
        </div>
      </div>
    </div>
  );
}

export default SupportChatPage;
