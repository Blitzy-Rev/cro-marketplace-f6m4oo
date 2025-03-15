/**
 * Utility module for molecular structure visualization and manipulation
 * using ChemDoodle Web Components.
 * 
 * This module provides functions for rendering and interacting with
 * 2D and 3D molecular structures in the frontend.
 */

import { Molecule } from '../types/molecule.types';
import ChemDoodle from 'chemdoodle-web'; // version 9.0.0

/**
 * Interface for ChemDoodle viewer configuration options
 */
export interface ViewerOptions {
  width?: number;
  height?: number;
  background?: string;
  bondLength_2D?: number;
  angstromsPerBondLength?: number;
  bonds_width_2D?: number;
  bonds_saturationWidth_2D?: number;
  bonds_hashSpacing_2D?: number;
  atoms_font_size_2D?: number;
  atoms_font_families_2D?: string[];
  atoms_useJMOLColors?: boolean;
  atoms_displayTerminalCarbonLabels_2D?: boolean;
  atoms_implicitHydrogens_2D?: boolean;
  shapes_color?: string;
  shapes_lineWidth?: number;
  compass_display?: boolean;
  compass_size?: number;
  compass_displayText?: boolean;
}

/**
 * Interface for image export options
 */
export interface ExportOptions {
  width?: number;
  height?: number;
  background?: string;
  transparent?: boolean;
}

/**
 * Interface for ChemDoodle viewer object
 */
export interface ChemDoodleViewer {
  loadMolecule: (molecule: ChemDoodleMolecule) => void;
  clear: () => void;
  center: () => void;
  repaint: () => void;
  getMolecules: () => ChemDoodleMolecule[];
  width: number;
  height: number;
  background: string;
}

/**
 * Interface for ChemDoodle molecule object
 */
export interface ChemDoodleMolecule {
  atoms: Array<any>;
  bonds: Array<any>;
}

/**
 * Default configuration options for ChemDoodle viewers
 */
export const DEFAULT_VIEWER_OPTIONS: ViewerOptions = {
  width: 300,
  height: 300,
  background: '#ffffff',
  bondLength_2D: 20,
  angstromsPerBondLength: 1.25,
  bonds_width_2D: 1,
  bonds_saturationWidth_2D: 2.5,
  bonds_hashSpacing_2D: 2.5,
  atoms_font_size_2D: 12,
  atoms_font_families_2D: ['Helvetica', 'Arial', 'sans-serif'],
  atoms_displayTerminalCarbonLabels_2D: true,
  atoms_useJMOLColors: true,
  atoms_implicitHydrogens_2D: true,
  shapes_color: '#000000',
  shapes_lineWidth: 1,
  compass_display: false,
  compass_size: 50,
  compass_displayText: false
};

/**
 * Creates and initializes a ChemDoodle viewer instance
 * @param container - HTML element to contain the viewer
 * @param options - Configuration options for the viewer
 * @param viewerType - Type of viewer to create ('2D' or '3D')
 * @returns Initialized ChemDoodle viewer instance
 */
export function createMoleculeViewer(
  container: HTMLElement,
  options: ViewerOptions = {},
  viewerType: string = '2D'
): ChemDoodleViewer {
  // Merge provided options with defaults
  const mergedOptions = { ...DEFAULT_VIEWER_OPTIONS, ...options };
  
  let viewer: ChemDoodleViewer;
  
  // Create appropriate viewer type
  if (viewerType === '3D') {
    viewer = new ChemDoodle.TransformCanvas3D(
      container.id,
      mergedOptions.width,
      mergedOptions.height
    );
    
    // Apply 3D specific options
    if (mergedOptions.angstromsPerBondLength) {
      viewer.angstromsPerBondLength = mergedOptions.angstromsPerBondLength;
    }
  } else {
    // Default to 2D viewer
    viewer = new ChemDoodle.ViewerCanvas(
      container.id,
      mergedOptions.width,
      mergedOptions.height
    );
    
    // Apply 2D specific options
    if (mergedOptions.bondLength_2D) {
      viewer.bondLength = mergedOptions.bondLength_2D;
    }
  }
  
  // Apply common options
  if (mergedOptions.background) {
    viewer.background = mergedOptions.background;
  }
  
  // Apply atom display options
  if (mergedOptions.atoms_useJMOLColors !== undefined) {
    viewer.atoms_useJMOLColors = mergedOptions.atoms_useJMOLColors;
  }
  
  if (mergedOptions.atoms_displayTerminalCarbonLabels_2D !== undefined && viewerType === '2D') {
    viewer.atoms_displayTerminalCarbonLabels = mergedOptions.atoms_displayTerminalCarbonLabels_2D;
  }
  
  if (mergedOptions.atoms_implicitHydrogens_2D !== undefined && viewerType === '2D') {
    viewer.atoms_implicitHydrogens = mergedOptions.atoms_implicitHydrogens_2D;
  }
  
  // Set up event handlers if needed
  viewer.repaint();
  
  return viewer;
}

/**
 * Loads a molecule into a ChemDoodle viewer from a SMILES string
 * @param viewer - ChemDoodle viewer instance
 * @param smiles - SMILES string representation of the molecule
 * @returns Promise resolving to true if loading was successful, false otherwise
 */
export async function loadMoleculeFromSmiles(
  viewer: ChemDoodleViewer,
  smiles: string
): Promise<boolean> {
  try {
    // Validate SMILES string
    if (!validateSmiles(smiles)) {
      console.error('Invalid SMILES string:', smiles);
      return false;
    }
    
    // Convert SMILES to molecule object based on viewer type
    let molecule: ChemDoodleMolecule;
    
    if (viewer instanceof ChemDoodle.TransformCanvas3D) {
      molecule = await convertSmilesTo3D(smiles);
    } else {
      molecule = await convertSmilesTo2D(smiles);
    }
    
    // Clear current content and load the new molecule
    viewer.clear();
    viewer.loadMolecule(molecule);
    
    // Center the view on the molecule
    viewer.center();
    viewer.repaint();
    
    return true;
  } catch (error) {
    console.error('Error loading molecule from SMILES:', error);
    return false;
  }
}

/**
 * Converts a SMILES string to a 2D ChemDoodle molecule object
 * @param smiles - SMILES string representation of the molecule
 * @returns Promise resolving to a ChemDoodle molecule object
 */
export async function convertSmilesTo2D(smiles: string): Promise<ChemDoodleMolecule> {
  return new Promise((resolve, reject) => {
    try {
      // Validate SMILES string
      if (!validateSmiles(smiles)) {
        reject(new Error('Invalid SMILES string'));
        return;
      }
      
      // Convert SMILES to molecule using ChemDoodle's parser
      const molecule = ChemDoodle.readSMILES(smiles);
      
      // Generate 2D coordinates
      ChemDoodle.iChemLabs.generateCoordinates(molecule, '2D', () => {
        resolve(molecule);
      }, (error: any) => {
        reject(new Error(`Failed to generate 2D coordinates: ${error}`));
      });
    } catch (error) {
      reject(error);
    }
  });
}

/**
 * Converts a SMILES string to a 3D ChemDoodle molecule object
 * @param smiles - SMILES string representation of the molecule
 * @returns Promise resolving to a ChemDoodle molecule object with 3D coordinates
 */
export async function convertSmilesTo3D(smiles: string): Promise<ChemDoodleMolecule> {
  return new Promise((resolve, reject) => {
    try {
      // Validate SMILES string
      if (!validateSmiles(smiles)) {
        reject(new Error('Invalid SMILES string'));
        return;
      }
      
      // Convert SMILES to molecule using ChemDoodle's parser
      const molecule = ChemDoodle.readSMILES(smiles);
      
      // Generate 3D coordinates
      ChemDoodle.iChemLabs.generateCoordinates(molecule, '3D', () => {
        // Apply force field optimization to improve 3D structure
        ChemDoodle.iChemLabs.optimize(molecule, () => {
          resolve(molecule);
        }, (error: any) => {
          reject(new Error(`Failed to optimize 3D structure: ${error}`));
        });
      }, (error: any) => {
        reject(new Error(`Failed to generate 3D coordinates: ${error}`));
      });
    } catch (error) {
      reject(error);
    }
  });
}

/**
 * Exports the current molecule view as an SVG string
 * @param viewer - ChemDoodle viewer instance
 * @param options - Export options (width, height, background, etc.)
 * @returns SVG representation of the molecule
 */
export function exportMoleculeToSVG(
  viewer: ChemDoodleViewer,
  options: ExportOptions = {}
): string {
  try {
    // Validate that viewer contains a molecule
    const molecule = getMoleculeFromViewer(viewer);
    
    if (!molecule) {
      throw new Error('No molecule to export');
    }
    
    // Set up export options
    const exportWidth = options.width || viewer.width;
    const exportHeight = options.height || viewer.height;
    const exportBackground = options.background || viewer.background;
    
    // Create a temporary canvas for export
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = exportWidth;
    tempCanvas.height = exportHeight;
    tempCanvas.id = 'temp-export-canvas';
    document.body.appendChild(tempCanvas);
    
    // Create a temporary viewer for export
    const exportViewer = new ChemDoodle.ViewerCanvas('temp-export-canvas', exportWidth, exportHeight);
    exportViewer.loadMolecule(molecule);
    exportViewer.background = exportBackground;
    exportViewer.repaint();
    
    // Export to SVG
    const svgString = ChemDoodle.io.toBinaryString(exportViewer, 'svg');
    
    // Clean up
    document.body.removeChild(tempCanvas);
    
    return svgString;
  } catch (error) {
    console.error('Error exporting molecule to SVG:', error);
    return '';
  }
}

/**
 * Exports the current molecule view as a PNG data URL
 * @param viewer - ChemDoodle viewer instance
 * @param options - Export options (width, height, background, etc.)
 * @returns Promise resolving to a data URL containing the PNG image
 */
export async function exportMoleculeToPNG(
  viewer: ChemDoodleViewer,
  options: ExportOptions = {}
): Promise<string> {
  return new Promise((resolve, reject) => {
    try {
      // Validate that viewer contains a molecule
      const molecule = getMoleculeFromViewer(viewer);
      
      if (!molecule) {
        reject(new Error('No molecule to export'));
        return;
      }
      
      // Set up export options
      const exportWidth = options.width || viewer.width;
      const exportHeight = options.height || viewer.height;
      const exportBackground = options.transparent ? 'transparent' : options.background || viewer.background;
      
      // Create a temporary canvas for export
      const tempCanvas = document.createElement('canvas');
      tempCanvas.width = exportWidth;
      tempCanvas.height = exportHeight;
      tempCanvas.id = 'temp-export-canvas';
      document.body.appendChild(tempCanvas);
      
      // Create a temporary viewer for export
      const exportViewer = new ChemDoodle.ViewerCanvas('temp-export-canvas', exportWidth, exportHeight);
      exportViewer.loadMolecule(molecule);
      exportViewer.background = exportBackground;
      
      // Force a repaint to ensure the molecule is rendered
      exportViewer.repaint();
      
      // Export to PNG data URL
      const dataURL = tempCanvas.toDataURL('image/png');
      
      // Clean up
      document.body.removeChild(tempCanvas);
      
      resolve(dataURL);
    } catch (error) {
      reject(error);
    }
  });
}

/**
 * Retrieves the current molecule object from a ChemDoodle viewer
 * @param viewer - ChemDoodle viewer instance
 * @returns The molecule object or null if no molecule is loaded
 */
export function getMoleculeFromViewer(viewer: ChemDoodleViewer): ChemDoodleMolecule | null {
  try {
    const molecules = viewer.getMolecules();
    
    if (molecules && molecules.length > 0) {
      return molecules[0];
    }
    
    return null;
  } catch (error) {
    console.error('Error retrieving molecule from viewer:', error);
    return null;
  }
}

/**
 * Validates a SMILES string for correct format and structure
 * @param smiles - SMILES string to validate
 * @returns True if the SMILES string is valid, false otherwise
 */
export function validateSmiles(smiles: string): boolean {
  try {
    // Check if input is a non-empty string
    if (!smiles || typeof smiles !== 'string' || smiles.trim() === '') {
      return false;
    }
    
    // Attempt to parse the SMILES string using ChemDoodle's parser
    const molecule = ChemDoodle.readSMILES(smiles);
    
    // Check if parsing was successful (molecule has atoms)
    return molecule && Array.isArray(molecule.atoms) && molecule.atoms.length > 0;
  } catch (error) {
    console.error('SMILES validation error:', error);
    return false;
  }
}