import { useState, useEffect, useCallback } from 'react';
import { fetchUserCertificates } from '../../../api/courses_api';
import EmptyCertificatesAlert from './EmptyCertificatesAlert/EmptyCertificatesAlert';
import CertificateSection from './CertificateSection/CertificateSection';
import './UserCertificatesPage.css';

/** Формат даты как в шаблоне: "d.m.Y в H:i" */
function formatCertificateDate(isoString) {
  if (!isoString) return '';
  const d = new Date(isoString);
  const day = String(d.getDate()).padStart(2, '0');
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const year = d.getFullYear();
  const hours = String(d.getHours()).padStart(2, '0');
  const minutes = String(d.getMinutes()).padStart(2, '0');
  return `${day}.${month}.${year} в ${hours}:${minutes}`;
}

const UserCertificatesPage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchUserCertificates();
      setData(result);
    } catch (err) {
      setError(err.message || 'Ошибка загрузки сертификатов');
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    document.title = 'Мои сертификаты';
    return () => { document.title = 'Главная'; };
  }, []);

  const totalCount = data?.total_count ?? 0;
  const hasCertificates = totalCount > 0;

  return (
    <main className="user-certificates-page" aria-label="Мои сертификаты">
      <div className="user-certificates-page__container">
        <header className="user-certificates-page__header">
          <h1 className="user-certificates-page__title">
            <span className="user-certificates-page__title-icon" aria-hidden="true">📜</span> Мои сертификаты
          </h1>
          {!loading && !error && (
            <span className="user-certificates-page__badge" aria-label={`Всего сертификатов: ${totalCount}`}>
              Всего: {totalCount}
            </span>
          )}
        </header>

        {loading && (
          <p className="user-certificates-page__loading" aria-live="polite">
            Загрузка сертификатов…
          </p>
        )}

        {error && (
          <p className="user-certificates-page__error" role="alert">
            {error}
          </p>
        )}

        {!loading && !error && data && (
          <>
            {!hasCertificates ? (
              <EmptyCertificatesAlert />
            ) : (
              <>
                <CertificateSection
                  title="Сертификаты за курсы"
                  iconLabel="📚"
                  certificates={data.course_certificates}
                  variant="course"
                  formatIssuedAt={formatCertificateDate}
                />
                <CertificateSection
                  title="Сертификаты за траектории"
                  iconLabel="🛤"
                  certificates={data.trajectory_certificates}
                  variant="trajectory"
                  formatIssuedAt={formatCertificateDate}
                />
              </>
            )}
          </>
        )}
      </div>
    </main>
  );
};

export default UserCertificatesPage;
