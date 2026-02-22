import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import HomePage from './components/HomePage/HomePage';
import './App.css';
import LoginPage from './components/UsersApp/LoginPage/LoginPage';
import LogoutPage from './components/UsersApp/LogoutPage/LogoutPage';
import AboutPage from './components/AboutPage/AboutPage';
import ShopPage from './components/ShopApp/ShopPage';
import OrderHistoryPage from './components/ShopApp/OrderHistoryPage/OrderHistoryPage';
import UsersWithOrdersPage from './components/ShopApp/UsersWithOrdersPage/UsersWithOrdersPage';
import UserOrdersAdminPage from './components/ShopApp/UserOrdersAdminPage/UserOrdersAdminPage';
import CreateProductPage from './components/ShopApp/CreateProductPage/CreateProductPage';
import ProfilePage from './components/UsersApp/UserProfilePage/ProfilePage';
import TransactionsPage from './components/UsersApp/TransactionsPage/TransactionsPage';
import QuizAttemptsReportPage from './components/UsersApp/QuizAttemptsReportPage/QuizAttemptsReportPage';
import DashboardPage from './components/DashboardPage/DashboardPage';
import ChangeLogPage from './components/ChangeLogPage/ChangeLogPage';
import MessengerPage from './components/MessengerApp/MessengerPage/MessengerPage';
import ChatRoomPage from './components/MessengerApp/ChatRoomPage/ChatRoomPage';
import UserListPage from './components/UserManagementApp/UserListPage/UserListPage';
import UserCreateStep1Page from './components/UserManagementApp/UserCreateStep1Page/UserCreateStep1Page';
import UserCreateStep2Page from './components/UserManagementApp/UserCreateStep2Page/UserCreateStep2Page';
import UserEditPage from './components/UserManagementApp/UserEditPage/UserEditPage';
import UserPasswordChangePage from './components/UserManagementApp/UserPasswordChangePage/UserPasswordChangePage';
import AdminDascoinDashboardPage from './components/UserManagementApp/AdminDascoinDashboardPage/AdminDascoinDashboardPage';
import AdminUserTransactionsPage from './components/UserManagementApp/AdminUserTransactionsPage/AdminUserTransactionsPage';
import KnowledgeBasePage from './components/BuilderApp/KnowledgeBasePage/KnowledgeBasePage';
import TrajectoryManagementPage from './components/BuilderApp/TrajectoryManagementPage/TrajectoryManagementPage';
import UserCertificatesPage from './components/CoursesApp/UserCertificatesPage/UserCertificatesPage';
import UserTrajectoryListPage from './components/CoursesApp/UserTrajectoryListPage/UserTrajectoryListPage';

const App = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path='/about' element={<AboutPage />}/>
          <Route path='/changelog' element={<ChangeLogPage />}/>
          <Route path='/builder' element={<DashboardPage />}/>
          <Route path='/builder/content' element={<KnowledgeBasePage />}/>
          <Route path='/builder/trajectory-management' element={<TrajectoryManagementPage />}/>
          <Route path='/builder/trajectory-management/' element={<TrajectoryManagementPage />}/>
          

          {/* shop */}
          <Route path='/shop/catalog' element={<ShopPage />}/>
          <Route path='/shop/history' element={<OrderHistoryPage />} />
          <Route path='/shop/admin/users' element={<UsersWithOrdersPage />} />
          <Route path='/shop/admin/user/:userId/orders' element={<UserOrdersAdminPage />} />
          <Route path='/shop/product/create' element={<CreateProductPage />} />

          {/* courses */}
          <Route path='/courses/trajectories' element={<UserTrajectoryListPage />} />
          <Route path='/courses/user-certificates' element={<UserCertificatesPage />} />

          {/* users */}
          <Route path='/users/login' element={<LoginPage />}/>
          <Route path='/users/logout' element={<LogoutPage />}/>
          <Route path='/users/profile' element={<ProfilePage />} />
          <Route path='/users/profile/transactions' element={<TransactionsPage />} />
          <Route path='/users/profile/quiz-attempts-report' element={<QuizAttemptsReportPage />} />

          {/* messenger */}
          <Route path='/messenger/chat/rooms' element={<MessengerPage />}/>
          <Route path='/messenger/chat/room/:roomId' element={<ChatRoomPage />}/>

          {/* user management */}
          <Route path='/user_management/users' element={<UserListPage />} />
          <Route path='/user_management/users/add/step1' element={<UserCreateStep1Page />} />
          <Route path='/user_management/users/add/step2' element={<UserCreateStep2Page />} />
          <Route path='/user_management/users/:userId/edit' element={<UserEditPage />} />
          <Route path='/user_management/user/:userId/password' element={<UserPasswordChangePage />} />
          <Route path='/user_management/admin/dascoin_dashboard/' element={<AdminDascoinDashboardPage />} />
          <Route path='/user_management/admin/user/:userId/transactions/' element={<AdminUserTransactionsPage />} />

          {/* Добавляйте новые маршруты здесь */}
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
