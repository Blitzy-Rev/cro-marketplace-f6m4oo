import React from 'react'; // React v18.0.0
import { Routes, Route, Navigate } from 'react-router-dom'; // react-router-dom v6.4.0

// Internal imports
import PrivateRoute from './PrivateRoute';
import PublicRoute from './PublicRoute';
import { ROUTES } from '../constants/routes';
import DashboardPage from '../pages/dashboard/DashboardPage';
import LoginPage from '../pages/auth/LoginPage';
import RegisterPage from '../pages/auth/RegisterPage';
import PasswordResetPage from '../pages/auth/PasswordResetPage';
import MoleculeLibraryPage from '../pages/molecule/MoleculeLibraryPage';
import MoleculeUploadPage from '../pages/molecule/MoleculeUploadPage';
import MoleculeDetailPage from '../pages/molecule/MoleculeDetailPage';
import MoleculeComparisonPage from '../pages/molecule/MoleculeComparisonPage';
import LibraryListPage from '../pages/library/LibraryListPage';
import LibraryDetailPage from '../pages/library/LibraryDetailPage';
import SubmissionListPage from '../pages/submission/SubmissionListPage';
import SubmissionFormPage from '../pages/submission/SubmissionFormPage';
import SubmissionDetailPage from '../pages/submission/SubmissionDetailPage';
import ResultsListPage from '../pages/results/ResultsListPage';
import ResultsUploadPage from '../pages/results/ResultsUploadPage';
import ResultsDetailPage from '../pages/results/ResultsDetailPage';
import CRODashboardPage from '../pages/cro/CRODashboardPage';
import CROListPage from '../pages/cro/CROListPage';
import CRODetailPage from '../pages/cro/CRODetailPage';
import ProfilePage from '../pages/user/ProfilePage';
import SettingsPage from '../pages/user/SettingsPage';
import NotFoundPage from '../pages/error/NotFoundPage';
import ServerErrorPage from '../pages/error/ServerErrorPage';
import AccessDeniedPage from '../pages/error/AccessDeniedPage';
import { SYSTEM_ADMIN, PHARMA_ADMIN, PHARMA_SCIENTIST, CRO_ADMIN, CRO_TECHNICIAN, PHARMA_ROLES, CRO_ROLES } from '../constants/userRoles';

/**
 * Main component that defines all application routes with appropriate access controls
 * @returns {JSX.Element} The complete routing configuration for the application
 */
const RouteConfig: React.FC = () => {
  return (
    <Routes>
      {/* Define the root route that redirects to dashboard or login based on authentication */}
      <Route path={ROUTES.ROOT} element={<Navigate to={ROUTES.DASHBOARD.ROOT} />} />

      {/* Define public routes for authentication (login, register, password reset) */}
      <Route element={<PublicRoute />}>
        <Route path={ROUTES.AUTH.LOGIN} element={<LoginPage />} />
        <Route path={ROUTES.AUTH.REGISTER} element={<RegisterPage />} />
        <Route path={ROUTES.AUTH.PASSWORD_RESET} element={<PasswordResetPage />} />
      </Route>

      {/* Define private routes for the main application features with role-based protection */}
      <Route element={<PrivateRoute requiredRoles={[SYSTEM_ADMIN, ...PHARMA_ROLES, ...CRO_ROLES]} />}>
        {/* Define molecule management routes (library, upload, detail, comparison) */}
        <Route path={ROUTES.MOLECULES.ROOT} element={<MoleculeLibraryPage />} />
        <Route path={ROUTES.MOLECULES.UPLOAD} element={<MoleculeUploadPage />} />
        <Route path={ROUTES.MOLECULES.DETAIL} element={<MoleculeDetailPage />} />
        <Route path={ROUTES.MOLECULES.COMPARISON} element={<MoleculeComparisonPage />} />

        {/* Define library management routes (list, detail) */}
        <Route path={ROUTES.LIBRARIES.ROOT} element={<LibraryListPage />} />
        <Route path={ROUTES.LIBRARIES.DETAIL} element={<LibraryDetailPage />} />

        {/* Define submission management routes (list, form, detail) */}
        <Route path={ROUTES.SUBMISSIONS.ROOT} element={<SubmissionListPage />} />
        <Route path={ROUTES.SUBMISSIONS.CREATE} element={<SubmissionFormPage />} />
        <Route path={ROUTES.SUBMISSIONS.DETAIL} element={<SubmissionDetailPage />} />

        {/* Define results management routes (list, upload, detail) */}
        <Route path={ROUTES.RESULTS.ROOT} element={<ResultsListPage />} />
        <Route path={ROUTES.RESULTS.UPLOAD} element={<ResultsUploadPage />} />
        <Route path={ROUTES.RESULTS.DETAIL} element={<ResultsDetailPage />} />

        {/* Define CRO-specific routes with appropriate role protection */}
        <Route element={<PrivateRoute requiredRoles={[SYSTEM_ADMIN, CRO_ADMIN, CRO_TECHNICIAN]} />}>
          <Route path={ROUTES.CRO.DASHBOARD} element={<CRODashboardPage />} />
        </Route>
        <Route element={<PrivateRoute requiredRoles={[SYSTEM_ADMIN, PHARMA_ADMIN, PHARMA_SCIENTIST]} />}>
          <Route path={ROUTES.CRO.LIST} element={<CROListPage />} />
          <Route path={ROUTES.CRO.DETAIL} element={<CRODetailPage />} />
        </Route>

        {/* Define user profile and settings routes */}
        <Route path={ROUTES.USER.PROFILE} element={<ProfilePage />} />
        <Route path={ROUTES.USER.SETTINGS} element={<SettingsPage />} />
      </Route>

      {/* Define error routes (not found, server error, access denied) */}
      <Route path={ROUTES.ERROR.NOT_FOUND} element={<NotFoundPage />} />
      <Route path={ROUTES.ERROR.SERVER_ERROR} element={<ServerErrorPage />} />
      <Route path={ROUTES.ERROR.ACCESS_DENIED} element={<AccessDeniedPage />} />
    </Routes>
  );
};

export default RouteConfig;