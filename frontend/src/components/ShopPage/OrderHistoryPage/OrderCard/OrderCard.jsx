import './OrderCard.css';

const STATUS_CLASS_MAP = {
  pending: 'order-card__status--pending',
  approved: 'order-card__status--approved',
  rejected: 'order-card__status--rejected',
  completed: 'order-card__status--completed',
  cancelled: 'order-card__status--cancelled',
};

const OrderCard = ({ order }) => {
  const statusClass = STATUS_CLASS_MAP[order.status] || '';

  return (
    <article className="order-card" aria-labelledby={`order-title-${order.id}`}>
      <div className="order-card__header">
        <div className="order-card__info">
          <h3 id={`order-title-${order.id}`} className="order-card__product-name">
            {order.product.name}
          </h3>
          <div className="order-card__meta">
            <span>
              <i className="fas fa-calendar" aria-hidden />
              {order.created_at}
            </span>
            <span>
              <i className="fas fa-coins" aria-hidden />
              <span className="order-card__points">{order.points_spent} баллов</span>
            </span>
            {order.reviewed_at && (
              <span>
                <i className="fas fa-check-circle" aria-hidden />
                Проверено: {order.reviewed_at}
              </span>
            )}
          </div>
        </div>
        <div className="order-card__status-wrap">
          <span className={`order-card__status ${statusClass}`}>{order.status_display}</span>
        </div>
      </div>
      {order.admin_comment && (
        <div className="order-card__admin-comment">
          <strong>
            <i className="fas fa-comment" aria-hidden /> Комментарий администратора:
          </strong>
          <p className="order-card__admin-comment-text">{order.admin_comment}</p>
        </div>
      )}
    </article>
  );
};

export default OrderCard;
