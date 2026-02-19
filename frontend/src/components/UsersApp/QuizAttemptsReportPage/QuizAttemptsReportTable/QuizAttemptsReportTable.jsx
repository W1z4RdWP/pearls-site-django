import { useState, useEffect } from 'react';
import './QuizAttemptsReportTable.css';

const QuizAttemptsReportTable = ({ reportData, selectedRowIndex, onRowClick, onRowDoubleClick }) => {
  const [clickTimeout, setClickTimeout] = useState(null);

  useEffect(() => {
    return () => {
      if (clickTimeout) {
        clearTimeout(clickTimeout);
      }
    };
  }, [clickTimeout]);

  const handleRowClick = (index, item, event) => {
    // Предотвращаем выделение при двойном клике
    if (event.detail === 2) {
      if (clickTimeout) {
        clearTimeout(clickTimeout);
        setClickTimeout(null);
      }
      return;
    }

    // Очищаем предыдущий таймаут
    if (clickTimeout) {
      clearTimeout(clickTimeout);
    }

    // Устанавливаем таймаут для обработки одиночного клика
    const timeout = setTimeout(() => {
      onRowClick(index);
      setClickTimeout(null);
    }, 200); // Задержка 200мс для различения одиночного и двойного клика

    setClickTimeout(timeout);
  };

  const handleRowDoubleClick = (item) => {
    if (clickTimeout) {
      clearTimeout(clickTimeout);
      setClickTimeout(null);
    }
    onRowDoubleClick(item);
  };

  const getStatusClassName = (statusSlug) => {
    return `quiz-attempts-report-table__status quiz-attempts-report-table__status--${statusSlug}`;
  };

  return (
    <div className="quiz-attempts-report-table-wrap">
      <table className="quiz-attempts-report-table" aria-label="Таблица попыток тестов и заданий">
        <thead className="quiz-attempts-report-table__head">
          <tr>
            <th className="quiz-attempts-report-table__th" style={{ width: '3%' }} title="Номер строки">
              #
            </th>
            <th className="quiz-attempts-report-table__th" style={{ width: '20%' }} title="Название">
              Название
            </th>
            <th className="quiz-attempts-report-table__th" style={{ width: '20%' }} title="Название курса">
              Название курса
            </th>
            <th className="quiz-attempts-report-table__th" style={{ width: '18%', textAlign: 'center' }} title="Тип">
              Тип
            </th>
            <th className="quiz-attempts-report-table__th" style={{ width: '13%', textAlign: 'center' }} title="Правильные ответы">
              Правильные ответы
            </th>
            <th className="quiz-attempts-report-table__th" style={{ width: '13%', textAlign: 'center' }} title="Процент">
              Процент
            </th>
            <th className="quiz-attempts-report-table__th" style={{ width: '13%', textAlign: 'center' }} title="Статус">
              Статус
            </th>
          </tr>
        </thead>
        <tbody>
          {reportData.map((item, index) => {
            const isSelected = selectedRowIndex === index;
            const isClickable = item.quiz_id && item.course_slug;
            const rowClassName = `quiz-attempts-report-table__row ${isSelected ? 'quiz-attempts-report-table__row--selected' : ''} ${isClickable ? 'quiz-attempts-report-table__row--clickable' : ''}`;

            return (
              <tr
                key={`${item.item_type}-${item.quiz_id || item.homework_id}-${index}`}
                className={rowClassName}
                onClick={isClickable ? (e) => handleRowClick(index, item, e) : undefined}
                onDoubleClick={isClickable ? () => handleRowDoubleClick(item) : undefined}
              >
                <td className="quiz-attempts-report-table__td" style={{ textAlign: 'center' }}>
                  {index + 1}
                </td>
                <td className="quiz-attempts-report-table__td">
                  {item.quiz_name}
                </td>
                <td className="quiz-attempts-report-table__td">
                  {item.course_name}
                </td>
                <td className="quiz-attempts-report-table__td" style={{ textAlign: 'center' }}>
                  {item.quiz_type}
                </td>
                <td className="quiz-attempts-report-table__td" style={{ textAlign: 'center' }}>
                  {item.item_type === 'homework' ? '—' : `${item.correct_count}/${item.total_count}`}
                </td>
                <td className="quiz-attempts-report-table__td" style={{ textAlign: 'center' }}>
                  {item.item_type === 'homework' ? (
                    <strong>—</strong>
                  ) : (
                    <strong>{item.percent}%</strong>
                  )}
                </td>
                <td className={`quiz-attempts-report-table__td ${getStatusClassName(item.status_slug)}`} style={{ textAlign: 'center' }}>
                  {item.status}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default QuizAttemptsReportTable;
