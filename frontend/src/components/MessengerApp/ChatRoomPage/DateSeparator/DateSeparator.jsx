import './DateSeparator.css';

const DateSeparator = ({ date }) => {
  const getDateText = (date) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const msgDate = new Date(date);
    msgDate.setHours(0, 0, 0, 0);
    
    const diffTime = today - msgDate;
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return 'Сегодня';
    } else if (diffDays === 1) {
      return 'Вчера';
    } else {
      const months = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
        'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'];
      return `${msgDate.getDate()} ${months[msgDate.getMonth()]} ${msgDate.getFullYear()}`;
    }
  };

  return (
    <div className="date-separator">
      <div className="date-separator__line">
        <span className="date-separator__text">
          {getDateText(date)}
        </span>
      </div>
    </div>
  );
};

export default DateSeparator;
