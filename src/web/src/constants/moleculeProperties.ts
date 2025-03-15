/**
 * Defines constants for molecular properties used throughout the frontend application
 * This file serves as the frontend counterpart to the backend's molecule_properties.py
 */

import { PropertyType, PropertyCategory } from '../types/molecule.types';

/**
 * Interface for molecular property definitions with metadata
 */
export interface PropertyDefinition {
  display_name: string;
  property_type: PropertyType;
  category: PropertyCategory;
  units?: string;
  description: string;
  is_required: boolean;
  is_filterable: boolean;
  is_predictable: boolean;
  min?: number;
  max?: number;
}

/**
 * Maps property keys to user-friendly display names for UI presentation
 */
export const PROPERTY_DISPLAY_NAMES: Record<string, string> = {
  smiles: 'SMILES',
  inchi_key: 'InChI Key',
  formula: 'Molecular Formula',
  molecular_weight: 'Molecular Weight',
  exact_mass: 'Exact Mass',
  logp: 'LogP',
  tpsa: 'TPSA',
  num_atoms: 'Atom Count',
  num_heavy_atoms: 'Heavy Atom Count',
  num_rings: 'Ring Count',
  num_rotatable_bonds: 'Rotatable Bonds',
  num_h_donors: 'H-Bond Donors',
  num_h_acceptors: 'H-Bond Acceptors',
  solubility: 'Solubility',
  melting_point: 'Melting Point',
  boiling_point: 'Boiling Point',
  pka: 'pKa',
  pkb: 'pKb',
  ic50: 'IC50',
  ec50: 'EC50',
  binding_affinity: 'Binding Affinity',
  permeability: 'Permeability',
  clearance: 'Clearance',
  half_life: 'Half-Life',
  bioavailability: 'Bioavailability',
  volume_of_distribution: 'Volume of Distribution',
  lipinski_violations: 'Lipinski Violations'
};

/**
 * Maps property keys to their standard units for consistent display
 */
export const PROPERTY_UNITS: Record<string, string> = {
  molecular_weight: 'g/mol',
  exact_mass: 'g/mol',
  logp: '',
  tpsa: 'Å²',
  solubility: 'mg/mL',
  melting_point: 'K',
  boiling_point: 'K',
  pka: '',
  pkb: '',
  ic50: 'nM',
  ec50: 'nM',
  binding_affinity: 'nM',
  permeability: 'cm/s',
  clearance: 'mL/min/kg',
  half_life: 'h',
  bioavailability: '%',
  volume_of_distribution: 'L/kg'
};

/**
 * Defines valid ranges for numeric properties for validation and filtering
 */
export const PROPERTY_RANGES: Record<string, { min: number; max: number }> = {
  molecular_weight: { min: 0, max: 2000 },
  exact_mass: { min: 0, max: 2000 },
  logp: { min: -10, max: 10 },
  tpsa: { min: 0, max: 500 },
  num_atoms: { min: 1, max: 1000 },
  num_heavy_atoms: { min: 1, max: 500 },
  num_rings: { min: 0, max: 50 },
  num_rotatable_bonds: { min: 0, max: 100 },
  num_h_donors: { min: 0, max: 50 },
  num_h_acceptors: { min: 0, max: 50 },
  solubility: { min: 0, max: 1000 },
  melting_point: { min: 0, max: 1000 },
  boiling_point: { min: 0, max: 1500 },
  pka: { min: -10, max: 20 },
  pkb: { min: -10, max: 20 },
  ic50: { min: 0, max: 1000000 },
  ec50: { min: 0, max: 1000000 },
  binding_affinity: { min: 0, max: 1000000 },
  permeability: { min: 0, max: 1 },
  clearance: { min: 0, max: 1000 },
  half_life: { min: 0, max: 100 },
  bioavailability: { min: 0, max: 100 },
  volume_of_distribution: { min: 0, max: 100 }
};

/**
 * List of properties required for all molecules
 */
export const REQUIRED_PROPERTIES: string[] = [
  'smiles',
  'inchi_key',
  'molecular_weight',
  'formula'
];

/**
 * List of properties that can be used for filtering in the UI
 */
export const FILTERABLE_PROPERTIES: string[] = [
  'molecular_weight',
  'logp',
  'tpsa',
  'num_rings',
  'num_rotatable_bonds',
  'num_h_donors',
  'num_h_acceptors',
  'solubility',
  'ic50',
  'ec50',
  'binding_affinity'
];

/**
 * List of properties that can be predicted by the AI engine
 */
export const PREDICTABLE_PROPERTIES: string[] = [
  'logp',
  'solubility',
  'permeability',
  'clearance',
  'half_life',
  'bioavailability',
  'ic50',
  'ec50',
  'binding_affinity',
  'pka',
  'pkb'
];

/**
 * Comprehensive definitions of standard molecular properties with metadata
 */
export const PROPERTY_DEFINITIONS: Record<string, PropertyDefinition> = {
  smiles: {
    display_name: 'SMILES',
    property_type: PropertyType.STRING,
    category: PropertyCategory.CHEMICAL,
    description: 'Simplified Molecular Input Line Entry System representation',
    is_required: true,
    is_filterable: true,
    is_predictable: false
  },
  inchi_key: {
    display_name: 'InChI Key',
    property_type: PropertyType.STRING,
    category: PropertyCategory.CHEMICAL,
    description: 'International Chemical Identifier Key',
    is_required: true,
    is_filterable: true,
    is_predictable: false
  },
  formula: {
    display_name: 'Molecular Formula',
    property_type: PropertyType.STRING,
    category: PropertyCategory.CHEMICAL,
    description: 'Chemical formula of the molecule',
    is_required: true,
    is_filterable: true,
    is_predictable: false
  },
  molecular_weight: {
    display_name: 'Molecular Weight',
    property_type: PropertyType.NUMERIC,
    category: PropertyCategory.PHYSICAL,
    units: 'g/mol',
    description: 'Average molecular mass of the molecule',
    is_required: true,
    is_filterable: true,
    is_predictable: true,
    min: 0,
    max: 2000
  },
  logp: {
    display_name: 'LogP',
    property_type: PropertyType.NUMERIC,
    category: PropertyCategory.PHYSICAL,
    description: 'Octanol-water partition coefficient',
    is_required: false,
    is_filterable: true,
    is_predictable: true,
    min: -10,
    max: 10
  },
  tpsa: {
    display_name: 'TPSA',
    property_type: PropertyType.NUMERIC,
    category: PropertyCategory.PHYSICAL,
    units: 'Å²',
    description: 'Topological polar surface area',
    is_required: false,
    is_filterable: true,
    is_predictable: true,
    min: 0,
    max: 500
  },
  solubility: {
    display_name: 'Solubility',
    property_type: PropertyType.NUMERIC,
    category: PropertyCategory.PHYSICAL,
    units: 'mg/mL',
    description: 'Aqueous solubility',
    is_required: false,
    is_filterable: true,
    is_predictable: true,
    min: 0,
    max: 1000
  },
  ic50: {
    display_name: 'IC50',
    property_type: PropertyType.NUMERIC,
    category: PropertyCategory.BIOLOGICAL,
    units: 'nM',
    description: 'Half maximal inhibitory concentration',
    is_required: false,
    is_filterable: true,
    is_predictable: true,
    min: 0,
    max: 1000000
  }
};