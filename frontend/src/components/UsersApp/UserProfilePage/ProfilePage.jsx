import { useCallback, useEffect, useState } from 'react';
import { fetchProfilePageData } from '../../../api/users_api';
import ProfileHeader from './ProfileHeader/ProfileHeader';
import ProfileActions from './ProfileActions/ProfileActions';
import ProfileEditForm from './ProfileEditForm/ProfileEditForm';
import GamificationSection from './GamificationSection/GamificationSection';
import './ProfilePage.css';

const ProfilePage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isEditing, setIsEditing] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = await fetchProfilePageData();
      setData(payload);
    } catch (err) {
      setData(null);
      setError(err);
      console.error('Error fetching profile:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleEditClick = () => {
    setIsEditing(true);
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
  };

  const handleUpdateSuccess = (updatedData) => {
    setData(updatedData);
    setIsEditing(false);
  };

  if (loading) {
    return (
      <main className="profile-page">
        <div className="profile-page__content">
          <p className="profile-page__loading">Загрузка...</p>
        </div>
      </main>
    );
  }

  if (error || !data) {
    return (
      <main className="profile-page">
        <div className="profile-page__content">
          <p className="profile-page__message">Войдите в аккаунт, чтобы видеть профиль.</p>
        </div>
      </main>
    );
  }

  return (
    <main className="profile-page" aria-label="Профиль пользователя">
      <div className="profile-page__content">
        {!isEditing && (
          <>
            <ProfileHeader
              user={data}
              profile={data.profile}
              dateJoined={data.date_joined}
              groups={data.groups}
            />
            <ProfileActions
              isExternal={data.is_external}
              onEditClick={handleEditClick}
              isEditing={isEditing}
            />
            <GamificationSection
              isExternal={data.is_external}
              recentBadges={data.recent_badges}
              totalBadges={data.total_badges}
              recentAchievements={data.recent_achievements}
              totalAchievements={data.total_achievements}
            />
          </>
        )}
        {isEditing && (
          <ProfileEditForm
            user={data}
            profile={data.profile}
            onSuccess={handleUpdateSuccess}
            onCancel={handleCancelEdit}
          />
        )}
      </div>
    </main>
  );
};

export default ProfilePage;
