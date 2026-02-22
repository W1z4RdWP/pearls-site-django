/**
 * Секция списка сертификатов (за курсы или за траектории).
 */
import CertificateCard from '../CertificateCard/CertificateCard';
import './CertificateSection.css';

const CertificateSection = ({ title, iconLabel, certificates, variant, formatIssuedAt }) => {
  if (!certificates || certificates.length === 0) return null;

  return (
    <section className={`certificate-section certificate-section--${variant}`} aria-labelledby={`certificate-section-${variant}`}>
      <div className="certificate-section__card">
        <header className="certificate-section__header">
          <h2 id={`certificate-section-${variant}`} className="certificate-section__title">
            <span className="certificate-section__icon" aria-hidden="true">{iconLabel}</span> {title}
          </h2>
        </header>
        <div className="certificate-section__body">
          <div className="certificate-section__grid">
            {certificates.map((cert) => (
              <CertificateCard
                key={cert.certificate_id}
                title={variant === 'course' ? cert.course?.title : cert.trajectory?.name}
                certificateId={cert.certificate_id}
                issuedAt={formatIssuedAt(cert.issued_at)}
                viewUrl={`/courses/certificate/${cert.certificate_id}/view/`}
                variant={variant}
              />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};

export default CertificateSection;
