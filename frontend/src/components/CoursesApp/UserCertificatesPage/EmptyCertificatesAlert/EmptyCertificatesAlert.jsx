import './EmptyCertificatesAlert.css';

/**
 * Сообщение при отсутствии сертификатов.
 */
const EmptyCertificatesAlert = () => (
  <div className="empty-certificates" role="status" aria-live="polite">
    <span className="empty-certificates__icon" aria-hidden="true">ℹ️</span>
    У вас пока нет сертификатов. Завершите курс или траекторию с включенной опцией «Сертификат», чтобы получить ваш первый сертификат!
  </div>
);

export default EmptyCertificatesAlert;
