import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom'; // react-router-dom v6.4.0
import { 
  Box, 
  Paper, 
  Typography, 
  Tabs, 
  Tab, 
  Button, 
  IconButton, 
  Tooltip, 
  Divider, 
  Grid, 
  CircularProgress,
  Alert
} from '@mui/material'; // @mui/material v5.0.0
import { styled } from '@mui/material/styles'; // @mui/material/styles v5.0.0
import { 
  Add, 
  Delete, 
  Download, 
  CompareArrows, 
  BarChart, 
  TableChart 
} from '@mui/icons-material'; // @mui/icons-material v5.0.0

import { 
  Molecule, 
  MoleculeProperty,
  PropertySource 
} from '../../types/molecule.types';
import MoleculeViewer from '../../components/molecule/MoleculeViewer';
import MoleculeCard from '../../components/molecule/MoleculeCard';
import PropertyTable from '../../components/molecule/PropertyTable';
import PropertyChart from '../../components/molecule/PropertyChart';
import DataTable from '../../components/common/DataTable';
import DashboardLayout from '../../components/layout/DashboardLayout';
import { getMolecule } from '../../api/moleculeApi';
import { formatMolecularProperty, getPropertyDisplayName } from '../../utils/propertyFormatters';

/**
 * Interface for processed comparison data
 */
interface ComparisonData {
  molecules: Record<string, Molecule>;
  propertyNames: string[];
  propertyMap: Record<string, Record<string, MoleculeProperty | null>>;
  differences: Record<string, boolean>;
}

/**
 * Styled container for the comparison page
 */
const ComparisonContainer = styled(Box)(theme => ({
  padding: theme.spacing(3),
  display: 'flex',
  flexDirection: 'column',
  gap: theme.spacing(3)
}));

/**
 * Styled header for the comparison page
 */
const ComparisonHeader = styled(Box)(theme => ({
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  marginBottom: theme.spacing(2)
}));

/**
 * Styled container for comparison control buttons
 */
const ComparisonControls = styled(Box)(theme => ({
  display: 'flex',
  gap: theme.spacing(1)
}));

/**
 * Styled grid for molecule structure comparison
 */
const MoleculeGrid = styled(Grid)(({ theme }) => ({
  marginTop: theme.spacing(2)
}));

/**
 * Styled grid item for individual molecule in comparison
 */
const MoleculeItem = styled(Grid)(({ theme }) => ({
  position: 'relative'
}));

/**
 * Styled button for removing a molecule from comparison
 */
const RemoveButton = styled(IconButton)(({ theme }) => ({
  position: 'absolute',
  top: '8px',
  right: '8px',
  zIndex: 1,
  backgroundColor: 'rgba(255, 255, 255, 0.7)',
  '&:hover': {
    backgroundColor: 'rgba(255, 255, 255, 0.9)'
  }
}));

/**
 * Styled component to highlight property differences
 */
const PropertyDifference = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'hasDifference'
})<{ hasDifference: boolean }>(({ theme, hasDifference }) => ({
  backgroundColor: hasDifference ? 'rgba(255, 152, 0, 0.1)' : 'transparent',
  fontWeight: hasDifference ? 'bold' : 'normal'
}));

/**
 * Styled component for empty comparison state
 */
const EmptyComparison = styled(Box)(theme => ({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  padding: theme.spacing(4),
  gap: theme.spacing(2)
}));

/**
 * Main component for the molecule comparison page
 */
const MoleculeComparisonPage: React.FC = () => {
  const { moleculeIds } = useParams<{ moleculeIds: string }>();
  const navigate = useNavigate();
  const location = useLocation();

  const [molecules, setMolecules] = useState<Record<string, Molecule>>({});
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('structure');

  // Extract molecule IDs from URL parameters
  const moleculeIdArray = useMemo(() => {
    return moleculeIds ? moleculeIds.split(',') : [];
  }, [moleculeIds]);

  // Fetch molecule data for each ID on component mount
  useEffect(() => {
    if (moleculeIdArray.length > 0) {
      fetchMoleculeData(moleculeIdArray);
    } else {
      setLoading(false);
    }
  }, [moleculeIdArray]);

  /**
   * Fetches molecule data for the given IDs
   */
  const fetchMoleculeData = async (moleculeIds: string[]) => {
    setLoading(true);
    setError(null);

    try {
      const moleculePromises = moleculeIds.map(id => getMolecule(id));
      const moleculeResults = await Promise.all(moleculePromises);

      const moleculeMap: Record<string, Molecule> = {};
      moleculeResults.forEach(result => {
        if (result.data) {
          moleculeMap[result.data.id] = result.data;
        }
      });

      setMolecules(moleculeMap);
    } catch (err: any) {
      setError(err.message || 'Failed to load molecules');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handles adding a new molecule to the comparison
   */
  const handleAddMolecule = useCallback((moleculeId: string) => {
    if (molecules[moleculeId]) return;

    const newMoleculeIds = moleculeIdArray.length > 0 ? [...moleculeIdArray, moleculeId] : [moleculeId];
    const newMoleculeIdsString = newMoleculeIds.join(',');

    navigate(`/molecules/compare/${newMoleculeIdsString}`);
  }, [molecules, moleculeIdArray, navigate]);

  /**
   * Handles removing a molecule from the comparison
   */
  const handleRemoveMolecule = useCallback((moleculeId: string) => {
    const newMoleculeIds = moleculeIdArray.filter(id => id !== moleculeId);
    const newMoleculeIdsString = newMoleculeIds.join(',');

    if (newMoleculeIdsString) {
      navigate(`/molecules/compare/${newMoleculeIdsString}`);
    } else {
      navigate('/molecules');
    }
  }, [moleculeIdArray, navigate]);

  /**
   * Handles exporting the comparison data
   */
  const handleExportComparison = () => {
    // Prepare comparison data in exportable format
    // Create a downloadable file (CSV or JSON)
    // Trigger file download
  };

  const comparisonData: ComparisonData | null = useMemo(() => {
    if (Object.keys(molecules).length === 0) return null;

    const moleculeArray = Object.values(molecules);
    if (moleculeArray.length === 0) return null;

    // Extract all unique property names across molecules
    const propertyNames = Array.from(new Set(moleculeArray.flatMap(molecule => molecule.properties?.map(prop => prop.name) || [])));

    // Create a map of molecule IDs to their properties
    const propertyMap: Record<string, Record<string, MoleculeProperty | null>> = {};
    moleculeArray.forEach(molecule => {
      propertyMap[molecule.id] = {};
      propertyNames.forEach(name => {
        const property = molecule.properties?.find(prop => prop.name === name) || null;
        propertyMap[molecule.id][name] = property;
      });
    });

    // Identify differences between molecules
    const differences: Record<string, boolean> = {};
    propertyNames.forEach(name => {
      const firstValue = moleculeArray[0].properties?.find(prop => prop.name === name)?.value;
      differences[name] = !moleculeArray.every(molecule => {
        return molecule.properties?.find(prop => prop.name === name)?.value === firstValue;
      });
    });

    return {
      molecules: molecules,
      propertyNames: propertyNames,
      propertyMap: propertyMap,
      differences: differences
    };
  }, [molecules]);

  /**
   * Renders the molecular structure comparison view
   */
  const renderStructureComparison = () => {
    if (!comparisonData) {
      return <EmptyComparison><Typography>No molecules selected for comparison.</Typography></EmptyComparison>;
    }

    return (
      <MoleculeGrid container spacing={3}>
        {Object.values(comparisonData.molecules).map(molecule => (
          <MoleculeItem item xs={12} sm={6} md={4} key={molecule.id}>
            <RemoveButton size="small" onClick={() => handleRemoveMolecule(molecule.id)}>
              <Delete />
            </RemoveButton>
            <MoleculeCard molecule={molecule} showActions={false} />
          </MoleculeItem>
        ))}
      </MoleculeGrid>
    );
  };

  /**
   * Renders the property table comparison view
   */
  const renderPropertyTableComparison = () => {
    if (!comparisonData) {
      return <EmptyComparison><Typography>No molecules selected for comparison.</Typography></EmptyComparison>;
    }

    const properties: MoleculeProperty[] = Object.values(comparisonData.molecules).flatMap(molecule => molecule.properties || []);

    return (
      <PropertyTable properties={properties} groupByCategory={true} />
    );
  };

  /**
   * Renders the property chart comparison view
   */
  const renderPropertyChartComparison = () => {
    if (!comparisonData) {
      return <EmptyComparison><Typography>No molecules selected for comparison.</Typography></EmptyComparison>;
    }

    const moleculesData: Record<string, MoleculeProperty[]> = {};
    Object.values(comparisonData.molecules).forEach(molecule => {
      moleculesData[molecule.id] = molecule.properties || [];
    });

    return (
      <PropertyChart properties={[]} compareMode={true} molecules={moleculesData} />
    );
  };

  return (
    <DashboardLayout title="Molecule Comparison">
      <ComparisonContainer>
        <ComparisonHeader>
          <Typography variant="h6">
            Comparing {Object.keys(molecules).length} Molecules
          </Typography>
          <ComparisonControls>
            <Button variant="contained" startIcon={<Add />} onClick={() => navigate('/molecules')}>
              Add Molecules
            </Button>
            <Button variant="outlined" startIcon={<Download />} onClick={handleExportComparison}>
              Export Comparison
            </Button>
          </ComparisonControls>
        </ComparisonHeader>

        {loading && <CircularProgress />}
        {error && <Alert severity="error">{error}</Alert>}

        <Tabs value={activeTab} onChange={(event, newValue) => setActiveTab(newValue)} aria-label="comparison tabs">
          <Tab label="Structure" value="structure" />
          <Tab label="Properties" value="properties" />
          <Tab label="Charts" value="charts" />
        </Tabs>

        {activeTab === 'structure' && renderStructureComparison()}
        {activeTab === 'properties' && renderPropertyTableComparison()}
        {activeTab === 'charts' && renderPropertyChartComparison()}
      </ComparisonContainer>
    </DashboardLayout>
  );
};

export default MoleculeComparisonPage;