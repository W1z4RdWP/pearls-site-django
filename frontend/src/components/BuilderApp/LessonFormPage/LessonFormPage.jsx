import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { CKEditor } from '@ckeditor/ckeditor5-react';
import {
  ClassicEditor,
  Essentials,
  Paragraph,
  Bold,
  Italic,
  Underline,
  Strikethrough,
  Code,
  Subscript,
  Superscript,
  Heading,
  Indent,
  IndentBlock,
  List,
  TodoList,
  ListProperties,
  BlockQuote,
  Link,
  CodeBlock,
  Highlight,
  FontSize,
  FontFamily,
  FontColor,
  FontBackgroundColor,
  RemoveFormat,
  Image,
  ImageUpload,
  ImageInsert,
  ImageStyle,
  ImageToolbar,
  ImageCaption,
  ImageResize,
  Table,
  TableToolbar,
  TableProperties,
  TableCellProperties,
  HtmlEmbed,
  SimpleUploadAdapter,
} from 'ckeditor5';
import 'ckeditor5/ckeditor5.css';
import {
  fetchLessonFormCreateData,
  createLesson,
  fetchLessonFormEditData,
  updateLesson,
} from '../../../api/builder_api';
import './LessonFormPage.css';

function getCsrfToken() {
  if (typeof document === 'undefined') return '';
  const match = document.cookie.match(/\bcsrftoken=([^;]+)/);
  return match ? match[1] : '';
}

const editorConfig = {
  licenseKey: 'GPL',
  language: 'ru',
  toolbar: {
    items: [
      '|', 'heading', '|', 'outdent', 'indent', '|',
      'bold', 'italic', 'underline', 'strikethrough', 'code', 'subscript', 'superscript', 'highlight', '|',
      'codeBlock', 'insertImage', 'bulletedList', 'numberedList', 'todoList', '|',
      'blockQuote', '|', 'fontSize', 'fontFamily', 'fontColor', 'fontBackgroundColor', 'removeFormat',
      'insertTable', '|', 'htmlEmbed', 'link', 'undo', 'redo',
    ],
    shouldNotGroupWhenFull: true,
  },
  image: {
    toolbar: ['|', 'imageTextAlternative', '|', 'imageStyle:alignLeft', 'imageStyle:alignRight', 'imageStyle:alignCenter', 'imageStyle:side', '|', 'toggleImageCaption', '|'],
    styles: ['full', 'side', 'alignLeft', 'alignRight', 'alignCenter'],
  },
  table: {
    contentToolbar: ['tableColumn', 'tableRow', 'mergeTableCells', 'tableProperties', 'tableCellProperties', 'toggleTableCaption'],
  },
  list: { properties: { styles: true, startIndex: true, reversed: true } },
  fontSize: { options: [9, 10, 11, 12, 13, 14, 15, 16, 'default', 18, 20, 22, 24, 28, 32, 36], supportAllValues: true },
  htmlSupport: {
    allow: [
      { name: 'img', attributes: { class: true, style: true } },
      { name: 'span', attributes: { style: true } },
      { name: 'table', attributes: ['style', 'width', 'height', 'border'] },
      { name: 'td', attributes: ['style', 'width', 'height', 'colspan', 'rowspan'] },
      { name: 'th', attributes: ['style', 'width', 'height', 'colspan', 'rowspan'] },
    ],
  },
  simpleUpload: {
    uploadUrl: typeof window !== 'undefined' ? new URL('/ckeditor5/image_upload/', window.location.origin).href : '',
    headers: { 'X-CSRFToken': getCsrfToken() },
    withCredentials: true,
  },
  plugins: [
    Essentials, Paragraph, Bold, Italic, Underline, Strikethrough, Code, Subscript, Superscript, Highlight,
    Heading, Indent, IndentBlock, CodeBlock, Image, ImageUpload, ImageInsert, ImageStyle, ImageToolbar,
    ImageCaption, ImageResize, List, TodoList, ListProperties, BlockQuote, FontSize, FontFamily, FontColor,
    FontBackgroundColor, RemoveFormat, Table, TableToolbar, TableProperties, TableCellProperties, HtmlEmbed, Link, SimpleUploadAdapter,
  ],
};

const LessonFormPage = () => {
  const { pk, categoryId } = useParams();
  const navigate = useNavigate();
  const isEdit = Boolean(pk);

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [order, setOrder] = useState(1);
  const [requiredTime, setRequiredTime] = useState(7);
  const [categoryIdVal, setCategoryIdVal] = useState('');
  const [courseIds, setCourseIds] = useState([]);
  const [finalQuizId, setFinalQuizId] = useState('');

  const [formErrors, setFormErrors] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (isEdit) {
        const result = await fetchLessonFormEditData(Number(pk));
        setData(result);
        const lesson = result.lesson;
        setTitle(lesson.title);
        setContent(lesson.content || '');
        setOrder(lesson.order);
        setRequiredTime(lesson.required_time ?? 7);
        setCategoryIdVal(lesson.category_id != null ? String(lesson.category_id) : '');
        setCourseIds(lesson.course_ids || []);
        setFinalQuizId(lesson.final_quiz_id != null ? String(lesson.final_quiz_id) : '');
      } else {
        const catId = categoryId != null ? Number(categoryId) : null;
        const result = await fetchLessonFormCreateData(catId);
        setData(result);
        setTitle('');
        setContent('');
        setRequiredTime(7);
        setCategoryIdVal(result.preselected_category ? String(result.preselected_category.id) : '');
        setCourseIds([]);
        setFinalQuizId('');
      }
    } catch (err) {
      setError(err.message || 'Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  }, [isEdit, pk, categoryId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    if (data && (isEdit ? data.lesson?.title : true)) {
      document.title = isEdit ? `Редактировать урок: ${data.lesson?.title}` : 'Добавить урок';
    }
    return () => { document.title = 'Главная'; };
  }, [data, isEdit]);

  const preselectedCategory = !isEdit && data?.preselected_category;
  const categories = data?.categories || [];
  const coursesChoices = data?.courses_choices ?? data?.courses ?? [];
  const quizzes = data?.quizzes || [];
  const cancelUrl = data?.cancel_url || '/builder/content/';

  const handleCourseIdsChange = useCallback((e) => {
    const options = e.target.options;
    const selected = [];
    for (let i = 0; i < options.length; i++) {
      if (options[i].selected) selected.push(Number(options[i].value));
    }
    setCourseIds(selected);
  }, []);

  const handleSubmit = useCallback(async (e) => {
    e.preventDefault();
    setFormErrors(null);
    setSubmitting(true);
    const payload = {
      title: title.trim(),
      content,
      required_time: Math.max(1, Math.min(999, Number(requiredTime) || 7)),
      category_id: categoryIdVal || null,
      course_ids: courseIds,
      final_quiz_id: finalQuizId || null,
    };
    if (isEdit) payload.order = Number(order) || 1;

    try {
      if (isEdit) {
        const result = await updateLesson(Number(pk), payload);
        if (result.success && result.redirect_url) {
          navigate(result.redirect_url);
        }
      } else {
        const result = await createLesson(payload, categoryId != null ? Number(categoryId) : null);
        if (result.success && result.redirect_url) {
          navigate(result.redirect_url);
        }
      }
    } catch (err) {
      if (err.errors) setFormErrors(err.errors);
      else setFormErrors({ _: [err.message || 'Ошибка сохранения'] });
    } finally {
      setSubmitting(false);
    }
  }, [isEdit, pk, categoryId, title, content, order, requiredTime, categoryIdVal, courseIds, finalQuizId, navigate]);

  const handleCancel = useCallback(() => {
    navigate(cancelUrl);
  }, [navigate, cancelUrl]);

  if (loading) {
    return (
      <main className="lesson-form-page" aria-label="Загрузка формы урока">
        <div className="lesson-form-page__container">
          <p className="lesson-form-page__loading" aria-live="polite">Загрузка…</p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="lesson-form-page" aria-label="Ошибка">
        <div className="lesson-form-page__container">
          <p className="lesson-form-page__error" role="alert">{error}</p>
        </div>
      </main>
    );
  }

  if (!data) return null;

  return (
    <main className="lesson-form-page" aria-label={isEdit ? 'Редактирование урока' : 'Добавление урока'}>
      <div className="lesson-form-page__container">
        <section className="lesson-form-page__section content-section">
          <h2 className="lesson-form-page__title">
            {isEdit ? 'Редактировать урок' : 'Добавить урок'}
          </h2>

          <form
            id="edit_lesson_form__builder"
            className="lesson-form-page__form"
            onSubmit={handleSubmit}
            noValidate
          >
            {formErrors && (
              <div className="lesson-form-page__form-errors" role="alert">
                {Object.entries(formErrors).map(([field, messages]) => (
                  <div key={field}>
                    {(Array.isArray(messages) ? messages : [messages]).map((msg, i) => (
                      <p key={i} className="lesson-form-page__form-error-msg">{msg}</p>
                    ))}
                  </div>
                ))}
              </div>
            )}

            {/* 1. Название (как в шаблоне: первое поле формы) */}
            <div className="lesson-form-page__field mb-3">
              <label htmlFor="lesson-form-title" className="lesson-form-page__label form-label">
                Название урока
              </label>
              <input
                id="lesson-form-title"
                type="text"
                className="lesson-form-page__input form-control"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                maxLength={200}
                required
                aria-required="true"
              />
              {formErrors?.title && (
                <div className="lesson-form-page__field-error text-danger">{formErrors.title[0]}</div>
              )}
            </div>

            {/* 2. Содержимое (в шаблоне: field.name === "content") */}
            <div className="lesson-form-page__field mb-3">
              <label htmlFor="lesson-form-content" className="lesson-form-page__label form-label">
                Содержимое
              </label>
              <div className="lesson-form-page__editor django-ckeditor-widget">
                <CKEditor
                  editor={ClassicEditor}
                  config={editorConfig}
                  data={content}
                  onChange={(event, editor) => setContent(editor.getData())}
                />
              </div>
              {formErrors?.content && (
                <div className="lesson-form-page__field-error text-danger">{formErrors.content[0]}</div>
              )}
            </div>

            {/* 3. Порядок — только при редактировании (как {% if form.instance.pk %} для order) */}
            {isEdit && (
              <div className="lesson-form-page__field mb-3">
                <label htmlFor="lesson-form-order" className="lesson-form-page__label form-label">
                  Порядок
                </label>
                <input
                  id="lesson-form-order"
                  type="number"
                  min={1}
                  className="lesson-form-page__input lesson-form-page__input--number form-control"
                  value={order}
                  onChange={(e) => setOrder(e.target.value)}
                />
                {formErrors?.order && (
                  <div className="lesson-form-page__field-error text-danger">{formErrors.order[0]}</div>
                )}
              </div>
            )}

            {/* 4. Курсы (как в шаблоне: courses) */}
            {coursesChoices.length > 0 && (
              <div className="lesson-form-page__field mb-3">
                <label htmlFor="lesson-form-courses" className="lesson-form-page__label form-label">
                  Выберите курсы, куда добавить урок
                </label>
                <select
                  id="lesson-form-courses"
                  multiple
                  className="lesson-form-page__select lesson-form-page__select--multiple form-select"
                  value={courseIds.map(String)}
                  onChange={handleCourseIdsChange}
                  aria-describedby="lesson-form-courses-hint"
                >
                  {coursesChoices.map((c) => (
                    <option key={c.id} value={c.id}>{c.title}</option>
                  ))}
                </select>
                <small id="lesson-form-courses-hint" className="lesson-form-page__hint form-text text-muted">
                  Выберите курсы, в которых будет использоваться этот урок
                </small>
                {formErrors?.courses && (
                  <div className="lesson-form-page__field-error text-danger">{formErrors.courses[0]}</div>
                )}
              </div>
            )}

            {/* 5. Категория: либо только чтение (preselected), либо select */}
            {preselectedCategory ? (
              <div className="lesson-form-page__field mb-3">
                <label className="lesson-form-page__label form-label">Категория</label>
                <input
                  type="text"
                  className="lesson-form-page__input lesson-form-page__input--plain form-control-plaintext"
                  readOnly
                  value={preselectedCategory.name}
                  aria-readonly="true"
                />
              </div>
            ) : categories.length > 0 ? (
              <div className="lesson-form-page__field mb-3">
                <label htmlFor="lesson-form-category" className="lesson-form-page__label form-label">
                  Категория
                </label>
                <select
                  id="lesson-form-category"
                  className="lesson-form-page__select form-select"
                  value={categoryIdVal}
                  onChange={(e) => setCategoryIdVal(e.target.value)}
                >
                  <option value="">— не выбрана —</option>
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
                {formErrors?.category_id && (
                  <div className="lesson-form-page__field-error text-danger">{formErrors.category_id[0]}</div>
                )}
              </div>
            ) : null}

            {/* 6. Необходимое время (минуты) */}
            <div className="lesson-form-page__field mb-3">
              <label htmlFor="lesson-form-required-time" className="lesson-form-page__label form-label">
                Необходимое время (минуты)
              </label>
              <input
                id="lesson-form-required-time"
                type="number"
                min={1}
                max={999}
                className="lesson-form-page__input lesson-form-page__input--number form-control"
                value={requiredTime}
                onChange={(e) => setRequiredTime(e.target.value)}
              />
              <small className="lesson-form-page__hint form-text text-muted">
                Время в минутах, необходимое для прохождения урока
              </small>
              {formErrors?.required_time && (
                <div className="lesson-form-page__field-error text-danger">{formErrors.required_time[0]}</div>
              )}
            </div>

            {/* 7. Финальный тест */}
            {quizzes.length > 0 && (
              <div className="lesson-form-page__field mb-3">
                <label htmlFor="lesson-form-final-quiz" className="lesson-form-page__label form-label">
                  Финальный тест
                </label>
                <select
                  id="lesson-form-final-quiz"
                  className="lesson-form-page__select form-select"
                  value={finalQuizId}
                  onChange={(e) => setFinalQuizId(e.target.value)}
                >
                  <option value="">— не выбран —</option>
                  {quizzes.map((q) => (
                    <option key={q.id} value={q.id}>{q.name}</option>
                  ))}
                </select>
                {formErrors?.final_quiz_id && (
                  <div className="lesson-form-page__field-error text-danger">{formErrors.final_quiz_id[0]}</div>
                )}
              </div>
            )}

            <div className="lesson-form-page__button-group button-group mt-4">
              <button
                type="submit"
                className="lesson-form-page__btn lesson-form-page__btn--primary btn btn-primary"
                disabled={submitting}
                aria-busy={submitting}
              >
                {submitting ? 'Сохранение…' : 'Сохранить'}
              </button>
              <button
                type="button"
                className="lesson-form-page__btn lesson-form-page__btn--secondary btn btn-secondary"
                onClick={handleCancel}
                disabled={submitting}
              >
                Отмена
              </button>
            </div>
          </form>
        </section>
      </div>
    </main>
  );
};

export default LessonFormPage;
