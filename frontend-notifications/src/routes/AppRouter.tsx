import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from '../components/NavBar';
import NotificationList from '../pages/NotificationList';
import AssignmentList from '../pages/AssignmentList';

const AppRouter = () => {
  return (
    <BrowserRouter>
      <Navbar />

      <Routes>
        <Route path="/" element={<Navigate to="/notifications" />} />

        <Route
          path="/notifications"
          element={<NotificationList />}
        />

        {/* Rutas futuras */}
        <Route path="/assignments" element={<AssignmentList />} />
      </Routes>
    </BrowserRouter>
  );
};

export default AppRouter;
