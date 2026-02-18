import { useState, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { createProduct } from '../../../../api/api';
import { CONSTRAINT_CHOICES } from '../CreateProductPage.constants';
import './CreateProductForm.css';

const CreateProductForm = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [pointsPrice, setPointsPrice] = useState('');
  const [constraints, setConstraints] = useState('');
  const [restrictionsText, setRestrictionsText] = useState('');
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [isActive, setIsActive] = useState(true);

  const [submitError, setSubmitError] = useState(null);
  const [fieldErrors, setFieldErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleImageChange = useCallback((e) => {
    const file = e.target.files?.[0];
    if (file) {
      setImageFile(file);
      const reader = new FileReader();
      reader.onload = (ev) => setImagePreview(ev.target?.result);
      reader.readAsDataURL(file);
    } else {
      setImageFile(null);
      setImagePreview(null);
    }
  }, []);

  const clearFieldError = useCallback((field) => {
    setFieldErrors((prev) => {
      const next = { ...prev };
      delete next[field];
      return next;
    });
  }, []);

  const handleSubmit = useCallback(
    async (e) => {
      e.preventDefault();
      setSubmitError(null);
      setFieldErrors({});
      setIsSubmitting(true);

      const formData = new FormData();
      formData.append('name', name.trim());
      if (description.trim()) formData.append('description', description.trim());
      formData.append('points_price', pointsPrice === '' ? '' : Number(pointsPrice));
      if (constraints) formData.append('constraints', constraints);
      if (restrictionsText.trim()) formData.append('restrictions_text', restrictionsText.trim());
      if (imageFile) formData.append('image', imageFile);
      if (isActive) formData.append('is_active', 'on');

      try {
        await createProduct(formData);
        navigate('/shop/catalog', { replace: true });
      } catch (err) {
        setSubmitError(err.message || 'Ошибка создания товара');
        if (err.errors && typeof err.errors === 'object') {
          setFieldErrors(err.errors);
        }
      } finally {
        setIsSubmitting(false);
      }
    },
    [name, description, pointsPrice, constraints, restrictionsText, imageFile, isActive, navigate]
  );

  const handleCancel = useCallback(() => {
    navigate('/shop/catalog');
  }, [navigate]);

  return (
    <div className="create-product-form-card">
      <form onSubmit={handleSubmit} className="create-product-form" noValidate>
        {submitError && (
          <div className="create-product-form__error" role="alert">
            {submitError}
          </div>
        )}

        <div className="create-product-form__group">
          <label htmlFor="product-name" className="create-product-form__label">
            Наименование товара *
          </label>
          <input
            id="product-name"
            type="text"
            className="create-product-form__input"
            placeholder="Введите название товара"
            value={name}
            onChange={(e) => {
              setName(e.target.value);
              clearFieldError('name');
            }}
            aria-invalid={Boolean(fieldErrors.name)}
            aria-describedby={fieldErrors.name ? 'product-name-error' : undefined}
          />
          {fieldErrors.name && (
            <div id="product-name-error" className="create-product-form__field-error">
              {fieldErrors.name[0]}
            </div>
          )}
        </div>

        <div className="create-product-form__group">
          <label htmlFor="product-description" className="create-product-form__label">
            Описание товара
          </label>
          <textarea
            id="product-description"
            className="create-product-form__textarea"
            rows={4}
            placeholder="Введите описание товара (необязательно)"
            value={description}
            onChange={(e) => {
              setDescription(e.target.value);
              clearFieldError('description');
            }}
            aria-invalid={Boolean(fieldErrors.description)}
          />
          {fieldErrors.description && (
            <div className="create-product-form__field-error">{fieldErrors.description[0]}</div>
          )}
        </div>

        <div className="create-product-form__group">
          <label htmlFor="product-points-price" className="create-product-form__label">
            Цена товара в баллах *
          </label>
          <input
            id="product-points-price"
            type="number"
            min={1}
            className="create-product-form__input"
            placeholder="Цена в баллах"
            value={pointsPrice}
            onChange={(e) => {
              setPointsPrice(e.target.value);
              clearFieldError('points_price');
            }}
            aria-invalid={Boolean(fieldErrors.points_price)}
          />
          {fieldErrors.points_price && (
            <div className="create-product-form__field-error">{fieldErrors.points_price[0]}</div>
          )}
        </div>

        <div className="create-product-form__group">
          <label htmlFor="product-constraints" className="create-product-form__label">
            Частота использования
          </label>
          <select
            id="product-constraints"
            className="create-product-form__select"
            value={constraints}
            onChange={(e) => {
              setConstraints(e.target.value);
              clearFieldError('constraints');
            }}
            aria-invalid={Boolean(fieldErrors.constraints)}
          >
            {CONSTRAINT_CHOICES.map((opt) => (
              <option key={opt.value || 'empty'} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
          {fieldErrors.constraints && (
            <div className="create-product-form__field-error">{fieldErrors.constraints[0]}</div>
          )}
        </div>

        <div className="create-product-form__group">
          <label htmlFor="product-restrictions" className="create-product-form__label">
            Ограничения (подробное описание)
          </label>
          <textarea
            id="product-restrictions"
            className="create-product-form__textarea"
            rows={3}
            placeholder="Подробное описание ограничений (необязательно)"
            value={restrictionsText}
            onChange={(e) => {
              setRestrictionsText(e.target.value);
              clearFieldError('restrictions_text');
            }}
            aria-invalid={Boolean(fieldErrors.restrictions_text)}
          />
          <div className="create-product-form__help">
            Например: &quot;1 раз в квартал (ограничение 2 сотрудника в отделении в 1 квартал) -
            ограничение по кол-ву заказов в 1 день - 1 заказ&quot;
          </div>
          {fieldErrors.restrictions_text && (
            <div className="create-product-form__field-error">
              {fieldErrors.restrictions_text[0]}
            </div>
          )}
        </div>

        <div className="create-product-form__group">
          <label htmlFor="product-image" className="create-product-form__label">
            Изображение товара
          </label>
          <input
            ref={fileInputRef}
            id="product-image"
            type="file"
            accept="image/*"
            className="create-product-form__file"
            onChange={handleImageChange}
            aria-invalid={Boolean(fieldErrors.image)}
          />
          <div className="create-product-form__help">
            Если не указано, будет использовано изображение по умолчанию
          </div>
          {imagePreview && (
            <img
              src={imagePreview}
              alt="Предпросмотр"
              className="create-product-form__preview"
            />
          )}
          {fieldErrors.image && (
            <div className="create-product-form__field-error">{fieldErrors.image[0]}</div>
          )}
        </div>

        <div className="create-product-form__group">
          <label className="create-product-form__checkbox-wrap">
            <input
              type="checkbox"
              className="create-product-form__checkbox"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              aria-invalid={Boolean(fieldErrors.is_active)}
            />
            <span className="create-product-form__checkbox-label">
              Активен (отображать в магазине)
            </span>
          </label>
          {fieldErrors.is_active && (
            <div className="create-product-form__field-error">{fieldErrors.is_active[0]}</div>
          )}
        </div>

        <div className="create-product-form__actions">
          <button
            type="button"
            className="create-product-form__btn create-product-form__btn--cancel"
            onClick={handleCancel}
            disabled={isSubmitting}
          >
            <i className="fas fa-times" aria-hidden />
            Отмена
          </button>
          <button
            type="submit"
            className="create-product-form__btn create-product-form__btn--primary"
            disabled={isSubmitting}
          >
            <i className="fas fa-save" aria-hidden />
            {isSubmitting ? 'Создание…' : 'Создать товар'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateProductForm;
