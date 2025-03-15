import React, { useRef, useState, useEffect } from 'react';
import { Box, CircularProgress, IconButton, Tooltip } from '@mui/material';
import { styled, useTheme } from '@mui/material/styles';
import { ThreeDRotation, ViewComfy, Download } from '@mui/icons-material';

import { Molecule } from '../../types/molecule.types';
import {
  createMoleculeViewer,
  loadMoleculeFromSmiles,
  DEFAULT_VIEWER_OPTIONS,
  exportMoleculeToSVG,
  exportMoleculeToPNG
} from '../../utils/moleculeStructure';

/**
 * Props for the MoleculeViewer component
 */
interface MoleculeViewerProps {
  /** SMILES representation of the molecule structure */
  smiles?: string;
  /** Molecule object containing SMILES and other data */
  molecule?: Molecule;
  /** Width of the viewer */
  width?: number | string;
  /** Height of the viewer */
  height?: number | string;
  /** Initial type of viewer to display */
  viewerType?: '2D' | '3D';
  /** Whether the viewer allows user interaction */
  interactive?: boolean;
  /** Whether to show control buttons for view toggle and export */
  showControls?: boolean;
  /** Callback when molecule loading completes */
  onLoad?: (success: boolean) => void;
  /** Additional CSS class name */
  className?: string;
}

/**
 * Interface for ChemDoodle viewer options
 */
interface ViewerOptions {
  /** Width of the viewer in pixels */
  width: number;
  /** Height of the viewer in pixels */
  height: number;
  /** Background color of the viewer */
  background?: string;
}

/**
 * Styled container for the molecule viewer
 */
const ViewerContainer = styled(Box)<{
  width: number | string;
  height: number | string;
}>(({ theme, width, height }) => ({
  width,
  height,
  position: 'relative',
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  backgroundColor: theme.palette.background.paper,
  borderRadius: theme.shape.borderRadius,
  overflow: 'hidden'
}));

/**
 * Container for viewer control buttons
 */
const ControlsContainer = styled(Box)(({ theme }) => ({
  position: 'absolute',
  top: '8px',
  right: '8px',
  display: 'flex',
  flexDirection: 'column',
  zIndex: 1,
  backgroundColor: 'rgba(255, 255, 255, 0.7)',
  borderRadius: theme.shape.borderRadius,
  padding: '4px'
}));

/**
 * Error message display for failed molecule loading
 */
const ErrorMessage = styled(Box)(({ theme }) => ({
  color: theme.palette.error.main,
  textAlign: 'center',
  padding: theme.spacing(2)
}));

/**
 * A component that renders a 2D or 3D visualization of a molecule using ChemDoodle Web Components
 */
const MoleculeViewer: React.FC<MoleculeViewerProps> = ({
  smiles,
  molecule,
  width = 300,
  height = 300,
  viewerType = '2D',
  interactive = true,
  showControls = true,
  onLoad,
  className
}) => {
  const theme = useTheme();
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<any>(null);
  const resizeTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<boolean>(false);
  const [currentViewType, setCurrentViewType] = useState<'2D' | '3D'>(viewerType);
  
  // Use SMILES from molecule prop if direct SMILES prop is not provided
  const smilesString = smiles || (molecule?.smiles || '');

  // Initialize the ChemDoodle viewer
  useEffect(() => {
    if (!containerRef.current) return;
    
    // Skip initialization if no SMILES data is available
    if (!smilesString) {
      setLoading(false);
      setError(true);
      if (onLoad) onLoad(false);
      return;
    }

    // Create a unique ID for the canvas element
    const containerId = `molecule-viewer-${Math.random().toString(36).substr(2, 9)}`;
    containerRef.current.id = containerId;
    
    // Parse dimensions
    const viewerWidth = typeof width === 'number' ? width : parseInt(width.toString(), 10);
    const viewerHeight = typeof height === 'number' ? height : parseInt(height.toString(), 10);
    
    // Initialize the viewer with appropriate options
    const options: ViewerOptions = {
      width: viewerWidth,
      height: viewerHeight,
      background: theme.palette.background.paper
    };
    
    // Create the viewer instance with interactive mode if specified
    const viewer = createMoleculeViewer(
      containerRef.current, 
      {
        ...options,
        // Additional options based on interactive flag could be added here
      }, 
      currentViewType
    );
    viewerRef.current = viewer;
    
    // Load the molecule from SMILES
    loadMolecule();
    
    // Handle resize events with debounce
    const handleResize = () => {
      // Clear existing timeout
      if (resizeTimeoutRef.current) {
        clearTimeout(resizeTimeoutRef.current);
      }
      
      // Set new timeout for debounce
      resizeTimeoutRef.current = setTimeout(() => {
        if (viewerRef.current && containerRef.current) {
          // ChemDoodle doesn't have a direct resize method
          // We need to reinitialize the viewer with new dimensions
          const container = containerRef.current;
          
          // Clean up existing canvas
          container.innerHTML = '';
          
          // Recreate viewer with new dimensions
          const newViewer = createMoleculeViewer(
            container, 
            {
              width: container.clientWidth,
              height: container.clientHeight,
              background: theme.palette.background.paper
            }, 
            currentViewType
          );
          
          viewerRef.current = newViewer;
          
          // Reload the molecule
          loadMoleculeFromSmiles(newViewer, smilesString);
        }
      }, 250); // 250ms debounce
    };
    
    // Add resize listener if component size is responsive
    if (typeof width === 'string' || typeof height === 'string') {
      window.addEventListener('resize', handleResize);
    }
    
    // Cleanup function
    return () => {
      // Remove event listener
      if (typeof width === 'string' || typeof height === 'string') {
        window.removeEventListener('resize', handleResize);
      }
      
      // Clear any pending timeouts
      if (resizeTimeoutRef.current) {
        clearTimeout(resizeTimeoutRef.current);
      }
      
      // ChemDoodle doesn't have a specific destroy method, but we can clean up the canvas
      if (containerRef.current) {
        containerRef.current.innerHTML = '';
      }
      viewerRef.current = null;
    };
  }, [currentViewType, smilesString, width, height, theme, interactive, onLoad]); // Re-initialize when these props change

  /**
   * Loads the molecule into the viewer
   */
  const loadMolecule = async () => {
    if (!viewerRef.current || !smilesString) {
      setError(true);
      setLoading(false);
      if (onLoad) onLoad(false);
      return;
    }
    
    setLoading(true);
    setError(false);
    
    try {
      const success = await loadMoleculeFromSmiles(viewerRef.current, smilesString);
      
      if (!success) {
        setError(true);
        if (onLoad) onLoad(false);
      } else {
        if (onLoad) onLoad(true);
      }
    } catch (err) {
      console.error('Error loading molecule:', err);
      setError(true);
      if (onLoad) onLoad(false);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Toggles between 2D and 3D views
   */
  const handleViewTypeToggle = () => {
    setCurrentViewType(currentViewType === '2D' ? '3D' : '2D');
  };

  /**
   * Exports the molecule as an SVG file
   */
  const handleExportSVG = () => {
    if (viewerRef.current) {
      const svgContent = exportMoleculeToSVG(viewerRef.current);
      
      if (svgContent) {
        // Create a blob URL and trigger download
        const blob = new Blob([svgContent], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `molecule-${Date.now()}.svg`;
        document.body.appendChild(a);
        a.click();
        
        // Clean up
        setTimeout(() => {
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        }, 100);
      }
    }
  };

  /**
   * Exports the molecule as a PNG file
   */
  const handleExportPNG = async () => {
    if (viewerRef.current) {
      try {
        const pngDataUrl = await exportMoleculeToPNG(viewerRef.current);
        
        if (pngDataUrl) {
          const a = document.createElement('a');
          a.href = pngDataUrl;
          a.download = `molecule-${Date.now()}.png`;
          document.body.appendChild(a);
          a.click();
          
          // Clean up
          setTimeout(() => {
            document.body.removeChild(a);
          }, 100);
        }
      } catch (err) {
        console.error('Error exporting PNG:', err);
      }
    }
  };

  return (
    <ViewerContainer 
      width={width} 
      height={height} 
      className={className}
      ref={containerRef}
      role="figure"
      aria-label="Molecule structure visualization"
    >
      {loading && (
        <CircularProgress 
          size={40} 
          sx={{ 
            position: 'absolute', 
            top: '50%', 
            left: '50%', 
            transform: 'translate(-50%, -50%)' 
          }} 
          aria-label="Loading molecule structure"
        />
      )}
      
      {error && !loading && (
        <ErrorMessage>
          Failed to load molecule structure
        </ErrorMessage>
      )}
      
      {showControls && !loading && !error && (
        <ControlsContainer>
          <Tooltip title={currentViewType === '2D' ? 'Switch to 3D View' : 'Switch to 2D View'}>
            <IconButton 
              size="small" 
              onClick={handleViewTypeToggle}
              aria-label={currentViewType === '2D' ? 'Switch to 3D View' : 'Switch to 2D View'}
            >
              {currentViewType === '2D' ? <ThreeDRotation /> : <ViewComfy />}
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Download as SVG">
            <IconButton 
              size="small" 
              onClick={handleExportSVG}
              aria-label="Download as SVG"
            >
              <Box display="flex" flexDirection="column" alignItems="center">
                <Download fontSize="small" />
                <Box component="span" fontSize="10px">SVG</Box>
              </Box>
            </IconButton>
          </Tooltip>
          
          <Tooltip title="Download as PNG">
            <IconButton 
              size="small" 
              onClick={handleExportPNG}
              aria-label="Download as PNG"
            >
              <Box display="flex" flexDirection="column" alignItems="center">
                <Download fontSize="small" />
                <Box component="span" fontSize="10px">PNG</Box>
              </Box>
            </IconButton>
          </Tooltip>
        </ControlsContainer>
      )}
    </ViewerContainer>
  );
};

export default MoleculeViewer;