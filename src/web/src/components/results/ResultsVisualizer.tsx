import React, { useState, useEffect, useMemo } from 'react';
import { Box, Typography, Tabs, Tab, FormControl, InputLabel, Select, MenuItem, Grid, Divider } from '@mui/material';
import { BarChart, ScatterPlot, BubbleChart, Timeline } from '@mui/icons-material';
import { styled, useTheme } from '@mui/material/styles';

import { Result, ResultProperty } from '../../types/result.types';
import { Molecule } from '../../types/molecule.types';
import PropertyChart from '../molecule/PropertyChart';
import MoleculeViewer from '../molecule/MoleculeViewer';
import { formatMolecularProperty, getPropertyDisplayName } from '../../utils/propertyFormatters';

// Define visualization types
interface VisualizationType {
  BAR_CHART: string;
  DISTRIBUTION: string;
  SCATTER_PLOT: string;
  MOLECULE_VIEW: string;
}

const VisualizationType: VisualizationType = {
  BAR_CHART: 'bar_chart',
  DISTRIBUTION: 'distribution',
  SCATTER_PLOT: 'scatter_plot',
  MOLECULE_VIEW: 'molecule_view'
};

// Interface for component props
interface ResultsVisualizerProps {
  result?: Result;
  properties?: ResultProperty[] | MoleculeProperty[];
  molecules?: Molecule[];
  width?: number | string;
  height?: number | string;
  className?: string;
}

// Styled components
const VisualizerContainer = styled(Box)<{
  width: number | string;
  height: number | string;
}>(({ width, height }) => ({
  width,
  height,
  display: 'flex',
  flexDirection: 'column',
  overflow: 'hidden'
}));

const ControlsContainer = styled(Box)(({ theme }) => ({
  marginBottom: theme.spacing(2)
}));

const VisualizationContainer = styled(Box)({
  flex: 1,
  overflow: 'hidden',
  position: 'relative'
});

const EmptyStateMessage = styled(Typography)(({ theme }) => ({
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  height: '100%',
  width: '100%'
}));

const MoleculeGrid = styled(Grid)({
  height: '100%',
  overflow: 'auto'
});

const MoleculeGridItem = styled(Grid)({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center'
});

/**
 * Component that provides interactive visualizations of experimental results data
 */
const ResultsVisualizer: React.FC<ResultsVisualizerProps> = ({
  result,
  properties,
  molecules,
  width = '100%',
  height = 600,
  className
}) => {
  const theme = useTheme();
  
  // State for selected visualization type
  const [visualizationType, setVisualizationType] = useState<string>(VisualizationType.BAR_CHART);
  
  // State for selected property
  const [selectedProperty, setSelectedProperty] = useState<string>('');
  
  // State for comparison property (for scatter plot)
  const [comparisonProperty, setComparisonProperty] = useState<string>('');
  
  // Process result data if direct properties aren't provided
  const processedProperties = useMemo(() => {
    if (properties) return properties;
    return result ? processResultProperties(result) : [];
  }, [result, properties]);
  
  // Get all molecules
  const allMolecules = useMemo(() => {
    if (molecules) return molecules;
    return result?.molecules || [];
  }, [result, molecules]);
  
  // Filter out only numeric properties for visualization
  const numericProperties = useMemo(() => {
    return getNumericProperties(processedProperties);
  }, [processedProperties]);
  
  // Create mapping of molecule IDs to properties for comparison
  const moleculePropertyMap = useMemo(() => {
    if (result) {
      return createMoleculePropertyMap(result);
    }
    return {};
  }, [result]);
  
  // Set initial property selection when data changes
  useEffect(() => {
    if (numericProperties.length > 0) {
      const uniqueProps = Array.from(new Set(numericProperties.map(prop => prop.name)));
      if (uniqueProps.length > 0) {
        setSelectedProperty(uniqueProps[0]);
        
        // Set comparison property to second property if available
        if (uniqueProps.length > 1) {
          setComparisonProperty(uniqueProps[1]);
        } else {
          setComparisonProperty(uniqueProps[0]);
        }
      }
    }
  }, [numericProperties]);
  
  // Handle visualization type change
  const handleVisualizationTypeChange = (event: React.SyntheticEvent, newValue: string) => {
    setVisualizationType(newValue);
  };
  
  // Handle property selection change
  const handlePropertyChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    setSelectedProperty(event.target.value as string);
  };
  
  // Handle comparison property change
  const handleComparisonPropertyChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    setComparisonProperty(event.target.value as string);
  };
  
  // Get unique property names for dropdowns
  const uniquePropertyNames = useMemo(() => {
    return Array.from(new Set(numericProperties.map(prop => prop.name)));
  }, [numericProperties]);
  
  // Determine PropertyChart chart type based on visualization type
  const getChartType = (visType: string) => {
    switch (visType) {
      case VisualizationType.BAR_CHART: return 'bar';
      case VisualizationType.DISTRIBUTION: return 'distribution';
      case VisualizationType.SCATTER_PLOT: return 'scatter';
      default: return 'bar';
    }
  };
  
  // Return empty state if no data is available
  if (numericProperties.length === 0) {
    return (
      <VisualizerContainer width={width} height={height} className={className}>
        <EmptyStateMessage variant="body1" color="text.secondary">
          No numeric properties available for visualization.
        </EmptyStateMessage>
      </VisualizerContainer>
    );
  }
  
  return (
    <VisualizerContainer width={width} height={height} className={className}>
      <ControlsContainer>
        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
          <Tabs
            value={visualizationType}
            onChange={handleVisualizationTypeChange}
            aria-label="Visualization type"
          >
            <Tab 
              icon={<BarChart />} 
              label="Bar Chart" 
              value={VisualizationType.BAR_CHART} 
              aria-label="Bar Chart"
            />
            <Tab 
              icon={<Timeline />} 
              label="Distribution" 
              value={VisualizationType.DISTRIBUTION} 
              aria-label="Distribution"
            />
            <Tab 
              icon={<ScatterPlot />} 
              label="Scatter Plot" 
              value={VisualizationType.SCATTER_PLOT} 
              aria-label="Scatter Plot"
            />
            <Tab 
              icon={<BubbleChart />} 
              label="Molecule View" 
              value={VisualizationType.MOLECULE_VIEW} 
              aria-label="Molecule View"
            />
          </Tabs>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <FormControl variant="outlined" size="small" sx={{ minWidth: 200 }}>
            <InputLabel id="property-select-label">Property</InputLabel>
            <Select
              labelId="property-select-label"
              id="property-select"
              value={selectedProperty}
              onChange={handlePropertyChange as any}
              label="Property"
            >
              {uniquePropertyNames.map((name) => (
                <MenuItem key={name} value={name}>
                  {getPropertyDisplayName(name)}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          
          {visualizationType === VisualizationType.SCATTER_PLOT && (
            <FormControl variant="outlined" size="small" sx={{ minWidth: 200 }}>
              <InputLabel id="comparison-property-select-label">Comparison Property</InputLabel>
              <Select
                labelId="comparison-property-select-label"
                id="comparison-property-select"
                value={comparisonProperty}
                onChange={handleComparisonPropertyChange as any}
                label="Comparison Property"
              >
                {uniquePropertyNames.map((name) => (
                  <MenuItem key={name} value={name}>
                    {getPropertyDisplayName(name)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
        </Box>
      </ControlsContainer>
      
      <VisualizationContainer>
        {(visualizationType === VisualizationType.BAR_CHART ||
          visualizationType === VisualizationType.DISTRIBUTION ||
          visualizationType === VisualizationType.SCATTER_PLOT) && (
          <PropertyChart 
            properties={
              visualizationType === VisualizationType.SCATTER_PLOT
                ? [
                    ...numericProperties.filter(p => p.name === selectedProperty),
                    ...numericProperties.filter(p => p.name === comparisonProperty)
                  ]
                : numericProperties.filter(p => p.name === selectedProperty)
            }
            chartType={getChartType(visualizationType)}
            height="100%"
            width="100%"
            showSource={true}
            showConfidence={true}
            compareMode={visualizationType === VisualizationType.SCATTER_PLOT}
            molecules={visualizationType === VisualizationType.SCATTER_PLOT ? moleculePropertyMap : undefined}
          />
        )}
        
        {visualizationType === VisualizationType.MOLECULE_VIEW && (
          <MoleculeGrid container spacing={2}>
            {allMolecules.map((molecule) => {
              const property = numericProperties.find(
                p => p.name === selectedProperty && 
                   ('molecule_id' in p ? p.molecule_id === molecule.id : true)
              );
              
              return (
                <MoleculeGridItem item xs={12} sm={6} md={4} lg={3} key={molecule.id}>
                  <MoleculeViewer 
                    molecule={molecule}
                    width={150}
                    height={150}
                    showControls={false}
                  />
                  <Typography variant="subtitle2" sx={{ mt: 1 }}>
                    {molecule.id}
                  </Typography>
                  {property && (
                    <Typography variant="body2" color="text.secondary">
                      {getPropertyDisplayName(selectedProperty)}: {formatMolecularProperty(property.value, selectedProperty)}
                    </Typography>
                  )}
                </MoleculeGridItem>
              );
            })}
          </MoleculeGrid>
        )}
      </VisualizationContainer>
    </VisualizerContainer>
  );
};

/**
 * Processes result properties into a format suitable for visualization
 */
function processResultProperties(result: Result): MoleculeProperty[] {
  if (!result || !result.properties) {
    return [];
  }
  
  return result.properties.map(prop => ({
    name: prop.name,
    value: prop.value,
    units: prop.units || undefined,
    source: 'EXPERIMENTAL'
  }));
}

/**
 * Creates a mapping of molecule IDs to their properties for comparison
 */
function createMoleculePropertyMap(result: Result): Record<string, MoleculeProperty[]> {
  const map: Record<string, MoleculeProperty[]> = {};
  
  if (!result || !result.properties) {
    return map;
  }
  
  result.properties.forEach(prop => {
    if (!map[prop.molecule_id]) {
      map[prop.molecule_id] = [];
    }
    
    map[prop.molecule_id].push({
      name: prop.name,
      value: prop.value,
      units: prop.units || undefined,
      source: 'EXPERIMENTAL'
    });
  });
  
  return map;
}

/**
 * Filters properties to only include those with numeric values
 */
function getNumericProperties(properties: any[]): MoleculeProperty[] {
  return properties.filter(prop => 
    prop.value !== null && 
    prop.value !== undefined && 
    !isNaN(Number(prop.value)) &&
    typeof prop.value !== 'boolean'
  );
}

export default ResultsVisualizer;