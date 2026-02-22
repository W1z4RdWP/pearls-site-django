import './CertificateCard.css';

/**
 * Карточка одного сертификата (курс или траектория).
 */
const CertificateCard = ({ title, certificateId, issuedAt, viewUrl, variant }) => {
  const isCourse = variant === 'course';
  const btnClass = isCourse ? 'certificate-card__btn certificate-card__btn--primary' : 'certificate-card__btn certificate-card__btn--success';
  const iconClass = isCourse ? 'certificate-card__icon certificate-card__icon--certificate' : 'certificate-card__icon certificate-card__icon--medal';

  const borderMod = isCourse ? 'certificate-card--primary' : 'certificate-card--success';
  return (
    <div className={`certificate-card ${borderMod}`}>
      <div className="certificate-card__body">
        <div className="certificate-card__main">
          <h6 className="certificate-card__title">{title}</h6>
          <p className="certificate-card__meta">
            <strong>№ {certificateId}</strong>
            <br />
            Выдан: {issuedAt}
          </p>
          <a href={viewUrl} className={btnClass} target="_blank" rel="noopener noreferrer" aria-label={`Просмотр сертификата ${title}`}>
            <span className="certificate-card__btn-icon" aria-hidden="true">👁</span> Просмотр
          </a>
        </div>
        <span className={iconClass} aria-hidden="true">{isCourse ? '📜' : '🏅'}</span>
      </div>
    </div>
  );
};

export default CertificateCard;
