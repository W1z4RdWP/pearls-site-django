import { useCallback, useEffect, useState } from 'react';
import { fetchUserData } from '../../../api/api';

const ProfilePage = () => {
    const [userData, setUserData] = useState(null);
    const [loading, setLoading] = useState(true);

    const loadUserData = useCallback(async () => {
        setLoading(true);
        try {
            const data = await fetchUserData();
            setUserData(data || null);
        } catch (err) {
            setUserData(null);
            console.error('Error fetching userData:', err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadUserData();
    }, [loadUserData]);

    if (loading) {
        return (
            <div className="profile-page">
                <p>Загрузка...</p>
            </div>
        );
    }

    if (!userData) {
        return (
            <div className="profile-page">
                <p>Войдите в аккаунт, чтобы видеть профиль.</p>
            </div>
        );
    }

    return (
        <div className="profile-page">
            <p>{userData.username}</p>
            {userData.email && <p>{userData.email}</p>}
        </div>
    );

}

export default ProfilePage;
