import React, { useEffect } from 'react';
import { Box } from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';

import CRODetail from '../../components/cro/CRODetail';
import { ROUTES, getCroDetailPath } from '../../constants/routes';
import { CROService } from '../../types/cro.types';
import useAuth from '../../hooks/useAuth';
import { SYSTEM_ADMIN, PHARMA_ADMIN, CRO_ADMIN } from '../../constants/userRoles';

/**
 * Page component that displays detailed information about a CRO service
 * Fetches the service data based on URL parameter and provides
 * functionality to edit or navigate back to the CRO list
 */
const CRODetailPage: React.FC = () => {
  // Extract id parameter from URL using useParams hook
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  // Check user permissions for editing CRO services
  const { hasPermission } = useAuth();
  const canEditCRO = hasPermission([SYSTEM_ADMIN, PHARMA_ADMIN, CRO_ADMIN]);

  // Redirect to list page if no ID is provided
  useEffect(() => {
    if (!id) {
      navigate(ROUTES.CRO.LIST);
    }
  }, [id, navigate]);

  // If no ID is provided, don't render anything while redirecting
  if (!id) {
    return null;
  }

  // Navigate back to CRO list page
  const handleBack = () => {
    navigate(ROUTES.CRO.LIST);
  };

  // Navigate to CRO edit page or trigger edit mode
  const handleEdit = (service: CROService) => {
    // The actual edit navigation or workflow would be implemented here
    // For example, it could navigate to an edit page or open an edit modal
    console.log('Edit CRO service:', service.id);
  };

  return (
    <Box sx={{ p: 3 }}>
      <CRODetail 
        serviceId={id} 
        onEdit={canEditCRO ? handleEdit : undefined}
        onBack={handleBack}
      />
    </Box>
  );
};

export default CRODetailPage;