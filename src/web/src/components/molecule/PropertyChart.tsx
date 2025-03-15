import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tooltip,
  CircularProgress
} from '@mui/material';
import { styled, useTheme } from '@mui/material/styles';
import * as d3 from 'd3'; // version ^7.8.5

import { MoleculeProperty, PropertySource } from '../../types/molecule.types';
import { 
  formatMolecularProperty, 
  getPropertyDisplayName,
  formatPredictionConfidence
} from '../../utils/propertyFormatters';
import { PROPERTY_UNITS, PROPERTY_RANGES } from '../../constants/moleculeProperties';

// Styled components
const ChartContainer = styled(Box)({
  width: '100%',
  height: '100%',
  display: 'flex',
  flexDirection: 'column'
});

const ChartControls = styled(Box)(({ theme }) => ({
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  marginBottom: theme.spacing(2)
}));

const ChartSvgContainer = styled(Box)({
  flex: 1,
  overflow: 'hidden',
  position: 'relative'
});

const ChartSvg = styled('svg')({
  width: '100%',
  height: '100%'
});

const EmptyChartMessage = styled(Typography)(({ theme }) => ({
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  height: '100%',
  width: '100%'
}));

const TooltipContent = styled(Box)(({ theme }) => ({
  padding: theme.spacing(1),
  backgroundColor: 'rgba(255, 255, 255, 0.9)',
  border: '1px solid',
  borderColor: theme.palette.divider,
  borderRadius: '4px',
  boxShadow: theme.shadows[1]
}));

// Enums
enum ChartType {
  BAR = 'bar',
  SCATTER = 'scatter',
  DISTRIBUTION = 'distribution'
}

// Interfaces
interface PropertyChartProps {
  properties: MoleculeProperty[];
  chartType?: ChartType;
  width?: number;
  height?: number;
  showSource?: boolean;
  showConfidence?: boolean;
  className?: string;
  compareMode?: boolean;
  molecules?: Record<string, MoleculeProperty[]>;
}

interface ProcessedPropertyData {
  propertyName: string;
  value: number;
  displayValue: string;
  source?: PropertySource;
  confidence?: number;
  moleculeId?: string;
  moleculeName?: string;
}

/**
 * Component that visualizes molecular property data using interactive charts
 */
const PropertyChart: React.FC<PropertyChartProps> = ({
  properties,
  chartType = ChartType.BAR,
  width = 600,
  height = 400,
  showSource = true,
  showConfidence = true,
  className,
  compareMode = false,
  molecules
}) => {
  const theme = useTheme();
  const svgRef = useRef<SVGSVGElement>(null);
  
  // Get only numeric properties for charting
  const numericProperties = useMemo(() => {
    return properties.filter(prop => 
      prop.value !== null && 
      prop.value !== undefined &&
      !isNaN(Number(prop.value)) &&
      typeof prop.value !== 'boolean'
    );
  }, [properties]);
  
  // Get unique property names
  const propertyNames = useMemo(() => {
    return Array.from(new Set(numericProperties.map(prop => prop.name)));
  }, [numericProperties]);
  
  // State for selected property
  const [selectedProperty, setSelectedProperty] = useState<string>(
    propertyNames.length > 0 ? propertyNames[0] : ''
  );
  
  // For scatter plot, we need a second property
  const [secondaryProperty, setSecondaryProperty] = useState<string>(
    propertyNames.length > 1 ? propertyNames[1] : ''
  );
  
  // Process property data for visualization
  const processedData = useMemo(() => {
    if (compareMode && molecules) {
      // Handle compare mode with multiple molecules
      const allData: ProcessedPropertyData[] = [];
      
      Object.entries(molecules).forEach(([moleculeId, moleculeProps]) => {
        const processed = processPropertyData(
          moleculeProps,
          selectedProperty,
          chartType
        );
        
        processed.forEach(item => {
          item.moleculeId = moleculeId;
          allData.push(item);
        });
      });
      
      return allData;
    } else {
      // Single molecule mode
      return processPropertyData(numericProperties, selectedProperty, chartType);
    }
  }, [numericProperties, selectedProperty, chartType, compareMode, molecules]);
  
  // Create and update D3 visualization
  useEffect(() => {
    if (!svgRef.current || !processedData.length || !selectedProperty) return;
    
    // Clear any existing chart
    d3.select(svgRef.current).selectAll('*').remove();
    
    // Draw the appropriate chart type
    switch (chartType) {
      case ChartType.BAR:
        createBarChart(svgRef.current, width, height, processedData, selectedProperty);
        break;
      case ChartType.SCATTER:
        if (secondaryProperty) {
          createScatterPlot(
            svgRef.current, 
            width, 
            height, 
            processedData, 
            selectedProperty, 
            secondaryProperty
          );
        }
        break;
      case ChartType.DISTRIBUTION:
        createDistributionPlot(svgRef.current, width, height, processedData, selectedProperty);
        break;
    }
    
    // Resize handler for responsiveness
    const handleResize = () => {
      if (!svgRef.current) return;
      
      const svg = d3.select(svgRef.current);
      svg.selectAll('*').remove();
      
      // Redraw the chart
      switch (chartType) {
        case ChartType.BAR:
          createBarChart(svgRef.current, width, height, processedData, selectedProperty);
          break;
        case ChartType.SCATTER:
          if (secondaryProperty) {
            createScatterPlot(
              svgRef.current, 
              width, 
              height, 
              processedData, 
              selectedProperty, 
              secondaryProperty
            );
          }
          break;
        case ChartType.DISTRIBUTION:
          createDistributionPlot(svgRef.current, width, height, processedData, selectedProperty);
          break;
      }
    };
    
    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, [processedData, selectedProperty, secondaryProperty, chartType, width, height]);
  
  // Handle property selection change
  const handlePropertyChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    setSelectedProperty(event.target.value as string);
  };
  
  // Handle secondary property selection (for scatter plot)
  const handleSecondaryPropertyChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    setSecondaryProperty(event.target.value as string);
  };
  
  // If there are no properties to display
  if (numericProperties.length === 0) {
    return (
      <EmptyChartMessage variant="body2" color="text.secondary">
        No numeric properties available for visualization.
      </EmptyChartMessage>
    );
  }
  
  // If the selected property doesn't exist
  if (selectedProperty && !propertyNames.includes(selectedProperty)) {
    setSelectedProperty(propertyNames[0]);
  }
  
  return (
    <ChartContainer className={className}>
      <ChartControls>
        <FormControl variant="outlined" size="small" style={{ minWidth: 200 }}>
          <InputLabel id="property-select-label">Property</InputLabel>
          <Select
            labelId="property-select-label"
            id="property-select"
            value={selectedProperty}
            onChange={handlePropertyChange as any}
            label="Property"
          >
            {propertyNames.map((name) => (
              <MenuItem key={name} value={name}>
                {getPropertyDisplayName(name)}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        
        {chartType === ChartType.SCATTER && (
          <FormControl variant="outlined" size="small" style={{ minWidth: 200 }}>
            <InputLabel id="secondary-property-select-label">Y-Axis Property</InputLabel>
            <Select
              labelId="secondary-property-select-label"
              id="secondary-property-select"
              value={secondaryProperty}
              onChange={handleSecondaryPropertyChange as any}
              label="Y-Axis Property"
            >
              {propertyNames.map((name) => (
                <MenuItem key={name} value={name}>
                  {getPropertyDisplayName(name)}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        )}
        
        {chartType === ChartType.BAR && (
          <Typography variant="caption" color="textSecondary">
            {showSource && (
              <>
                <span style={{ color: '#4caf50', fontWeight: 'bold', marginRight: 8 }}>● Experimental</span>
                <span style={{ color: '#2196f3', fontWeight: 'bold', marginRight: 8 }}>● Predicted</span>
                <span style={{ color: '#ff9800', fontWeight: 'bold' }}>● Calculated</span>
              </>
            )}
          </Typography>
        )}
      </ChartControls>
      
      <ChartSvgContainer>
        <ChartSvg ref={svgRef} />
      </ChartSvgContainer>
    </ChartContainer>
  );
};

/**
 * Processes raw property data into a format suitable for visualization
 */
function processPropertyData(
  properties: MoleculeProperty[],
  selectedProperty: string,
  chartType: ChartType
): ProcessedPropertyData[] {
  // Filter properties to only include the selected property and ensure they're numeric
  const filteredProps = properties.filter(
    (prop) => 
      prop.name === selectedProperty && 
      prop.value !== null && 
      prop.value !== undefined && 
      !isNaN(Number(prop.value))
  );
  
  // Convert to visualization format
  return filteredProps.map((prop) => {
    const numValue = Number(prop.value);
    return {
      propertyName: prop.name,
      value: numValue,
      displayValue: formatMolecularProperty(numValue, prop.name),
      source: prop.source,
      // Extract confidence from property if it exists
      confidence: prop.source === PropertySource.PREDICTED ? 
        (typeof prop.value === 'object' && prop.value && 'confidence' in prop.value ? 
          Number(prop.value.confidence) : undefined) : 
        undefined
    };
  });
}

/**
 * Creates a bar chart visualization for a single property across molecules
 */
function createBarChart(
  container: SVGElement,
  width: number,
  height: number,
  data: ProcessedPropertyData[],
  propertyName: string
): void {
  const svg = d3.select(container);
  const margin = { top: 30, right: 30, bottom: 70, left: 60 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  
  // Create chart group
  const g = svg
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`);
  
  // Add chart title
  g.append('text')
    .attr('class', 'chart-title')
    .attr('x', innerWidth / 2)
    .attr('y', -10)
    .attr('text-anchor', 'middle')
    .text(getPropertyDisplayName(propertyName));
  
  // X scale for molecules (categorical)
  const x = d3.scaleBand()
    .domain(data.map((d, i) => d.moleculeName || d.moleculeId || `Item ${i+1}`))
    .range([0, innerWidth])
    .padding(0.2);
  
  // Get property range for Y scale
  const propertyRange = getPropertyRange(propertyName, data);
  
  // Y scale (numerical)
  const y = d3.scaleLinear()
    .domain([
      Math.min(0, propertyRange.min), // Include 0 for reference
      propertyRange.max
    ])
    .nice()
    .range([innerHeight, 0]);
  
  // Add X axis
  g.append('g')
    .attr('class', 'x-axis')
    .attr('transform', `translate(0,${innerHeight})`)
    .call(d3.axisBottom(x))
    .selectAll('text')
    .attr('transform', 'rotate(-45)')
    .style('text-anchor', 'end')
    .attr('dx', '-.8em')
    .attr('dy', '.15em');
  
  // Add Y axis
  g.append('g')
    .attr('class', 'y-axis')
    .call(d3.axisLeft(y));
  
  // Add Y axis label with units
  const units = PROPERTY_UNITS[propertyName] || '';
  g.append('text')
    .attr('class', 'y-axis-label')
    .attr('transform', 'rotate(-90)')
    .attr('y', -margin.left + 20)
    .attr('x', -innerHeight / 2)
    .attr('text-anchor', 'middle')
    .text(units ? `${units}` : '');
  
  // Create bars
  const bars = g.selectAll('.bar')
    .data(data)
    .enter()
    .append('rect')
    .attr('class', 'bar')
    .attr('x', (d, i) => x(d.moleculeName || d.moleculeId || `Item ${i+1}`) || 0)
    .attr('width', x.bandwidth())
    .attr('y', d => y(Math.max(0, d.value)))
    .attr('height', d => Math.abs(y(d.value) - y(0)))
    .attr('fill', d => {
      // Color bars based on data source
      if (d.source === PropertySource.EXPERIMENTAL) {
        return '#4caf50'; // Green for experimental data
      } else if (d.source === PropertySource.PREDICTED) {
        return '#2196f3'; // Blue for predicted data
      } else if (d.source === PropertySource.CALCULATED) {
        return '#ff9800'; // Orange for calculated data
      } else {
        return '#9e9e9e'; // Grey for imported or unknown data
      }
    });
  
  // Add tooltips
  bars.append('title')
    .text(d => {
      let tooltip = `${d.displayValue}`;
      if (d.source) {
        tooltip += `\nSource: ${d.source}`;
      }
      if (d.source === PropertySource.PREDICTED && d.confidence !== undefined) {
        tooltip += `\nConfidence: ${(d.confidence * 100).toFixed(0)}%`;
      }
      return tooltip;
    });
  
  // Add confidence indicators for predicted properties
  g.selectAll('.confidence-indicator')
    .data(data.filter(d => d.source === PropertySource.PREDICTED && d.confidence !== undefined))
    .enter()
    .append('rect')
    .attr('class', 'confidence-indicator')
    .attr('x', (d, i) => {
      const barX = x(d.moleculeName || d.moleculeId || `Item ${i+1}`) || 0;
      return barX + x.bandwidth() / 4;
    })
    .attr('width', x.bandwidth() / 2)
    .attr('y', d => innerHeight + 5)
    .attr('height', 5)
    .attr('fill', d => {
      // Color based on confidence level
      if (d.confidence && d.confidence >= 0.8) {
        return '#4caf50'; // High confidence
      } else if (d.confidence && d.confidence >= 0.6) {
        return '#ff9800'; // Medium confidence
      } else {
        return '#f44336'; // Low confidence
      }
    });
}

/**
 * Creates a scatter plot visualization comparing two properties
 */
function createScatterPlot(
  container: SVGElement,
  width: number,
  height: number,
  data: ProcessedPropertyData[],
  xProperty: string,
  yProperty: string
): void {
  // Get all unique molecule IDs
  const moleculeIds = Array.from(new Set(data.map(d => d.moleculeId)));
  
  // Create paired data points for scatter plot
  const pairedData: {x: number, y: number, xSource?: PropertySource, ySource?: PropertySource, 
                     xConfidence?: number, yConfidence?: number, moleculeId?: string}[] = [];
  
  moleculeIds.forEach(id => {
    const xData = data.find(d => d.propertyName === xProperty && d.moleculeId === id);
    const yData = data.find(d => d.propertyName === yProperty && d.moleculeId === id);
    
    if (xData && yData) {
      pairedData.push({
        x: xData.value,
        y: yData.value,
        xSource: xData.source,
        ySource: yData.source,
        xConfidence: xData.confidence,
        yConfidence: yData.confidence,
        moleculeId: id
      });
    }
  });
  
  const svg = d3.select(container);
  const margin = { top: 30, right: 30, bottom: 70, left: 60 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  
  // Create chart group
  const g = svg
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`);
  
  // Add chart title
  g.append('text')
    .attr('class', 'chart-title')
    .attr('x', innerWidth / 2)
    .attr('y', -10)
    .attr('text-anchor', 'middle')
    .text(`${getPropertyDisplayName(xProperty)} vs ${getPropertyDisplayName(yProperty)}`);
  
  // Get range for X and Y properties
  const xRange = getPropertyRange(xProperty, data.filter(d => d.propertyName === xProperty));
  const yRange = getPropertyRange(yProperty, data.filter(d => d.propertyName === yProperty));
  
  // X scale
  const x = d3.scaleLinear()
    .domain([xRange.min, xRange.max])
    .nice()
    .range([0, innerWidth]);
  
  // Y scale
  const y = d3.scaleLinear()
    .domain([yRange.min, yRange.max])
    .nice()
    .range([innerHeight, 0]);
  
  // Add X axis
  g.append('g')
    .attr('class', 'x-axis')
    .attr('transform', `translate(0,${innerHeight})`)
    .call(d3.axisBottom(x));
  
  // Add Y axis
  g.append('g')
    .attr('class', 'y-axis')
    .call(d3.axisLeft(y));
  
  // Add X axis label with units
  const xUnits = PROPERTY_UNITS[xProperty] || '';
  g.append('text')
    .attr('class', 'x-axis-label')
    .attr('x', innerWidth / 2)
    .attr('y', innerHeight + margin.bottom - 10)
    .attr('text-anchor', 'middle')
    .text(`${getPropertyDisplayName(xProperty)}${xUnits ? ` (${xUnits})` : ''}`);
  
  // Add Y axis label with units
  const yUnits = PROPERTY_UNITS[yProperty] || '';
  g.append('text')
    .attr('class', 'y-axis-label')
    .attr('transform', 'rotate(-90)')
    .attr('y', -margin.left + 20)
    .attr('x', -innerHeight / 2)
    .attr('text-anchor', 'middle')
    .text(`${getPropertyDisplayName(yProperty)}${yUnits ? ` (${yUnits})` : ''}`);
  
  // Create scatter points
  g.selectAll('.point')
    .data(pairedData)
    .enter()
    .append('circle')
    .attr('class', 'point')
    .attr('cx', d => x(d.x))
    .attr('cy', d => y(d.y))
    .attr('r', 6)
    .attr('fill', d => {
      // Color based on source (giving priority to predicted values)
      if (d.xSource === PropertySource.PREDICTED || d.ySource === PropertySource.PREDICTED) {
        return '#2196f3'; // Blue for predicted
      } else if (d.xSource === PropertySource.EXPERIMENTAL || d.ySource === PropertySource.EXPERIMENTAL) {
        return '#4caf50'; // Green for experimental
      } else if (d.xSource === PropertySource.CALCULATED || d.ySource === PropertySource.CALCULATED) {
        return '#ff9800'; // Orange for calculated
      } else {
        return '#9e9e9e'; // Grey for imported/unknown
      }
    })
    .attr('opacity', 0.7)
    .attr('stroke', '#ffffff')
    .attr('stroke-width', 1);
  
  // Add tooltips
  g.selectAll('.point')
    .append('title')
    .text(d => {
      const xValue = formatMolecularProperty(d.x, xProperty);
      const yValue = formatMolecularProperty(d.y, yProperty);
      
      let tooltip = `${getPropertyDisplayName(xProperty)}: ${xValue}\n${getPropertyDisplayName(yProperty)}: ${yValue}`;
      
      // Add source and confidence information if available
      if (d.xSource) {
        tooltip += `\nX Source: ${d.xSource}`;
      }
      if (d.ySource) {
        tooltip += `\nY Source: ${d.ySource}`;
      }
      if (d.xSource === PropertySource.PREDICTED && d.xConfidence !== undefined) {
        tooltip += `\nX Confidence: ${(d.xConfidence * 100).toFixed(0)}%`;
      }
      if (d.ySource === PropertySource.PREDICTED && d.yConfidence !== undefined) {
        tooltip += `\nY Confidence: ${(d.yConfidence * 100).toFixed(0)}%`;
      }
      
      return tooltip;
    });
}

/**
 * Creates a distribution plot (histogram) for a single property
 */
function createDistributionPlot(
  container: SVGElement,
  width: number,
  height: number,
  data: ProcessedPropertyData[],
  propertyName: string
): void {
  // Extract values for the selected property
  const values = data
    .filter(d => d.propertyName === propertyName)
    .map(d => d.value);
  
  if (values.length === 0) {
    return;
  }
  
  const svg = d3.select(container);
  const margin = { top: 30, right: 30, bottom: 70, left: 60 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  
  // Create chart group
  const g = svg
    .append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`);
  
  // Add chart title
  g.append('text')
    .attr('class', 'chart-title')
    .attr('x', innerWidth / 2)
    .attr('y', -10)
    .attr('text-anchor', 'middle')
    .text(`Distribution of ${getPropertyDisplayName(propertyName)}`);
  
  // Get property range
  const propertyRange = getPropertyRange(propertyName, data);
  
  // X scale
  const x = d3.scaleLinear()
    .domain([propertyRange.min, propertyRange.max])
    .nice()
    .range([0, innerWidth]);
  
  // Create histogram generator
  const histogram = d3.bin<number, number>()
    .domain(x.domain())
    .thresholds(x.ticks(Math.min(20, Math.max(5, Math.ceil(Math.sqrt(values.length))))));
  
  // Generate bins
  const bins = histogram(values);
  
  // Y scale (for bin heights)
  const y = d3.scaleLinear()
    .domain([0, d3.max(bins, d => d.length) || 0])
    .nice()
    .range([innerHeight, 0]);
  
  // Add X axis
  g.append('g')
    .attr('class', 'x-axis')
    .attr('transform', `translate(0,${innerHeight})`)
    .call(d3.axisBottom(x));
  
  // Add Y axis
  g.append('g')
    .attr('class', 'y-axis')
    .call(d3.axisLeft(y));
  
  // Add X axis label with units
  const units = PROPERTY_UNITS[propertyName] || '';
  g.append('text')
    .attr('class', 'x-axis-label')
    .attr('x', innerWidth / 2)
    .attr('y', innerHeight + margin.bottom - 10)
    .attr('text-anchor', 'middle')
    .text(`${getPropertyDisplayName(propertyName)}${units ? ` (${units})` : ''}`);
  
  // Add Y axis label
  g.append('text')
    .attr('class', 'y-axis-label')
    .attr('transform', 'rotate(-90)')
    .attr('y', -margin.left + 20)
    .attr('x', -innerHeight / 2)
    .attr('text-anchor', 'middle')
    .text('Frequency');
  
  // Create histogram bars
  g.selectAll('.histogram-bar')
    .data(bins)
    .enter()
    .append('rect')
    .attr('class', 'histogram-bar')
    .attr('x', d => x(d.x0 || 0))
    .attr('width', d => Math.max(0, x(d.x1 || 0) - x(d.x0 || 0) - 1))
    .attr('y', d => y(d.length))
    .attr('height', d => innerHeight - y(d.length))
    .attr('fill', '#2196f3')
    .attr('opacity', 0.7);
  
  // Add density curve if there are enough data points
  if (values.length >= 10) {
    // Create density data
    const densityData = [];
    const thresholds = x.ticks(100);
    const bandwidth = 1.5 * (propertyRange.max - propertyRange.min) / Math.sqrt(values.length);
    
    for (let i = 0; i < thresholds.length; i++) {
      let sum = 0;
      for (let j = 0; j < values.length; j++) {
        const v = values[j];
        const z = (thresholds[i] - v) / bandwidth;
        sum += Math.exp(-0.5 * z * z) / Math.sqrt(2 * Math.PI);
      }
      densityData.push({ x: thresholds[i], y: sum / (values.length * bandwidth) });
    }
    
    // Scale density values to chart height
    const maxDensity = d3.max(densityData, d => d.y) || 0;
    const yDensityScale = d3.scaleLinear()
      .domain([0, maxDensity])
      .range([innerHeight, 0]);
    
    // Create the density line
    const line = d3.line<{x: number, y: number}>()
      .x(d => x(d.x))
      .y(d => yDensityScale(d.y))
      .curve(d3.curveMonotoneX);
    
    // Add the curve
    g.append('path')
      .datum(densityData)
      .attr('class', 'density-line')
      .attr('fill', 'none')
      .attr('stroke', '#ff9800')
      .attr('stroke-width', 2)
      .attr('d', line);
  }
  
  // Add tooltips for bars
  g.selectAll('.histogram-bar')
    .append('title')
    .text(d => {
      const rangeStart = formatMolecularProperty(d.x0 || 0, propertyName);
      const rangeEnd = formatMolecularProperty(d.x1 || 0, propertyName);
      return `Range: ${rangeStart} to ${rangeEnd}\nCount: ${d.length}`;
    });
}

/**
 * Gets the min and max range for a property, either from predefined ranges or from data
 */
function getPropertyRange(
  propertyName: string,
  data: ProcessedPropertyData[]
): { min: number; max: number } {
  // Check if we have a predefined range
  if (PROPERTY_RANGES[propertyName]) {
    return PROPERTY_RANGES[propertyName];
  }
  
  // Otherwise, calculate from data with some padding
  const values = data
    .filter(d => d.propertyName === propertyName)
    .map(d => d.value);
  
  if (values.length === 0) {
    return { min: 0, max: 1 }; // Default range if no data
  }
  
  const min = d3.min(values) || 0;
  const max = d3.max(values) || 1;
  
  // Add padding for better visualization (10% on each side)
  const padding = (max - min) * 0.1;
  
  return {
    min: min - padding,
    max: max + padding
  };
}

export default PropertyChart;