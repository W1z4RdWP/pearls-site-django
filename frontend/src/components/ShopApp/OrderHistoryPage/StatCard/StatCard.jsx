import './StatCard.css';

const StatCard = ({ value, label }) => {
  return (
    <div className="stat-card">
      <div className="stat-card__value">{value}</div>
      <div className="stat-card__label">{label}</div>
    </div>
  );
};

export default StatCard;
