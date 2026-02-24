import { request, getCSRFToken, API_BASE } from './api';

/**
 * Список траекторий пользователя и прогресс по курсам (все курсы без серверной фильтрации).
 * @returns {Promise<{ user_trajectories: Array, courses_data: Array, ...stats }>}
 */
export function fetchTrajectoryList() {
  return request('/courses/trajectories/');
}

/**
 * Список сертификатов текущего пользователя (по курсам и траекториям).
 * @returns {Promise<{ course_certificates: Array, trajectory_certificates: Array, total_count: number }>}
 */
export function fetchUserCertificates() {
  return request('/courses/user-certificates/');
}

/**
 * Полные данные страницы курса (детальная).
 * @param {string} slug — slug курса
 * @returns {Promise<object>}
 */
export function fetchCourseDetail(slug) {
  return request(`/courses/course/${slug}/`);
}

/**
 * Начать курс (переход из available в started).
 * @param {string} slug — slug курса
 * @returns {Promise<{success: boolean, status: string}>}
 */
export function startCourse(slug) {
  return request(`/courses/course/${slug}/start/`, {
    method: 'POST',
    body: JSON.stringify({}),
  });
}

/**
 * Данные страницы редактирования курса (форма: курс, группы, course_detail_url).
 * @param {string} slug — slug курса
 * @returns {Promise<{ course: object, groups: Array, course_detail_url: string }>}
 */
export function fetchCourseEditData(slug) {
  return request(`/courses/course/${encodeURIComponent(slug)}/edit/`);
}

/**
 * Сохранить изменения курса (FormData: title, description, image, slug, final_quiz, responsible_mentor,
 * mentors_time_to_check, allowed_groups[], certificate, is_incident, default_deadline_days).
 * @param {string} slug — slug курса
 * @param {FormData} formData
 * @returns {Promise<{ success: boolean, slug: string, redirect_url: string }>}
 */
export function updateCourse(slug, formData) {
  const config = {
    method: 'POST',
    credentials: 'include',
    headers: {
      'X-CSRFToken': getCSRFToken(),
    },
    body: formData,
  };
  return fetch(`${API_BASE}/courses/course/${encodeURIComponent(slug)}/edit/`, config).then(async (response) => {
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const err = new Error(data.error || `HTTP ${response.status}`);
      err.errors = data.errors;
      throw err;
    }
    return data;
  });
}

/**
 * Данные страницы редактирования урока (форма + курс, список курсов для выбора).
 * @param {number} lessonId — ID урока
 * @returns {Promise<{course: object|null, lesson: object, courses_choices: Array, cancel_url: string}>}
 */
export function fetchEditLessonData(lessonId) {
  return request(`/courses/lesson/${lessonId}/edit/`);
}

/**
 * Сохранить изменения урока.
 * @param {number} lessonId — ID урока
 * @param {object} data — { title, content, order, required_time, course_ids, final_quiz_id? }
 * @returns {Promise<{success: boolean, redirect_url: string}>}
 */
export function submitEditLesson(lessonId, data) {
  return request(`/courses/lesson/${lessonId}/edit/`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Данные страницы создания урока (курс, список курсов для выбора).
 * @param {string} slug — slug курса
 * @returns {Promise<{ course: { title, slug }, courses: Array<{ id, title }> }>}
 */
export function fetchCreateLessonPageData(slug) {
  return request(`/courses/course/${encodeURIComponent(slug)}/create-lesson/`);
}

/**
 * Создать урок в курсе.
 * @param {string} slug — slug курса
 * @param {object} data — { title, content?, required_time?, course_ids? }
 * @returns {Promise<{ success: boolean, lesson_id: number, redirect_url: string }>}
 */
export function createLesson(slug, data) {
  return request(`/courses/course/${encodeURIComponent(slug)}/create-lesson/`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Данные для модалки/страницы добавления материалов в курс (категории, уроки без категории, тесты, задания).
 * @param {string} slug — slug курса
 * @returns {Promise<{ course: object, categories_data: Array, uncategorized_lessons: Array, all_quizzes: Array, all_homeworks: Array }>}
 */
export function fetchAddLessonData(slug) {
  return request(`/courses/course/${encodeURIComponent(slug)}/add-lesson/`);
}

/**
 * Добавить выбранные материалы в курс (уроки, категории, тесты, задания).
 * @param {string} slug — slug курса
 * @param {string[]} selectedItems — массив id вида 'category_1', 'lesson_2', 'quiz_3', 'homework_4', 'uncategorized_5'
 * @returns {Promise<{ success: boolean, redirect_url: string }>}
 */
export function addLessonMaterials(slug, selectedItems) {
  return request(`/courses/course/${encodeURIComponent(slug)}/add-lesson/`, {
    method: 'POST',
    body: JSON.stringify({ selected_items: selectedItems }),
  });
}

/**
 * Данные страницы создания курса: группы, флаг is_incident.
 * @param {boolean} [isIncident=false]
 * @returns {Promise<{ groups: Array<{id: number, name: string}>, is_incident: boolean }>}
 */
export function fetchCreateCoursePageData(isIncident = false) {
  const qs = isIncident ? '?is_incident=1' : '';
  return request(`/courses/create-course/${qs}`);
}

/**
 * Создать курс (FormData: title, description, image, slug, final_quiz, responsible_mentor,
 * mentors_time_to_check, allowed_groups[], certificate, is_incident, is_incident_readonly?, default_deadline_days).
 * @param {FormData} formData
 * @returns {Promise<{ slug: string }>}
 */
export function createCourse(formData) {
  const config = {
    method: 'POST',
    credentials: 'include',
    headers: {
      'X-CSRFToken': getCSRFToken(),
    },
    body: formData,
  };
  return fetch(`${API_BASE}/courses/create-course/`, config).then(async (response) => {
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const err = new Error(data.error || `HTTP ${response.status}`);
      err.errors = data.errors;
      throw err;
    }
    return data;
  });
}

/**
 * Поиск наставников (для выбора ответственного в форме курса).
 * @param {string} q — поисковый запрос
 * @returns {Promise<{ users: Array<{id, full_name, username}> }>}
 */
export function searchMentors(q = '') {
  const params = new URLSearchParams({ mentor_only: 'true' });
  if (q && q.trim()) params.set('q', q.trim());
  return request(`/builder/users/search/?${params.toString()}`);
}

/**
 * Поиск тестов (для выбора финального теста курса).
 * @param {string} q — поисковый запрос
 * @returns {Promise<{ success: boolean, results: Array<{id, name, questions_count}> }>}
 */
export function searchQuizzes(q = '') {
  const params = q && q.trim() ? { q: q.trim() } : {};
  const qs = new URLSearchParams(params).toString();
  return request(`/quizzes/search/${qs ? `?${qs}` : ''}`);
}
