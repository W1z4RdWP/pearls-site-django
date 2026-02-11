import { useCallback, useEffect, useState } from 'react';
import { fetchProfilePageData } from '../../../api/api';
import ProfileHeader from './ProfileHeader/ProfileHeader';
import ProfileActions from './ProfileActions/ProfileActions';
import GamificationSection from './GamificationSection/GamificationSection';
import './ProfilePage.css';

const ProfilePage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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
        <ProfileHeader
          user={data}
          profile={data.profile}
          dateJoined={data.date_joined}
          groups={data.groups}
        />
        <ProfileActions isExternal={data.is_external} />
        <GamificationSection
          isExternal={data.is_external}
          recentBadges={data.recent_badges}
          totalBadges={data.total_badges}
          recentAchievements={data.recent_achievements}
          totalAchievements={data.total_achievements}
        />
      </div>
    </main>
  );
};

export default ProfilePage;
