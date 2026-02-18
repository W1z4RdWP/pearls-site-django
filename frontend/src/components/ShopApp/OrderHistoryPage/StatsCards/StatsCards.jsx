import StatCard from '../StatCard/StatCard';
import './StatsCards.css';

const StatsCards = ({ stats, totalPointsSpent, totalPointsRefunded }) => {
  if (!stats || stats.total === 0) return null;

  return (
    <section className="stats-cards" aria-label="Статистика заказов">
      <StatCard value={stats.total} label="Всего заказов" />
      <StatCard value={stats.pending} label="Ожидают" />
      <StatCard value={totalPointsSpent} label="Потрачено баллов" />
      <StatCard value={totalPointsRefunded} label="Возвращено баллов" />
    </section>
  );
};

export default StatsCards;
