from enum import Enum

class PropertyType(Enum):
    """Enumeration of property data types for validation and storage."""
    STRING = "string"
    NUMERIC = "numeric"
    INTEGER = "integer"
    BOOLEAN = "boolean"

class PropertySource(Enum):
    """Enumeration of property data sources for tracking data provenance."""
    CALCULATED = "calculated"
    IMPORTED = "imported"
    PREDICTED = "predicted"
    EXPERIMENTAL = "experimental"

class PropertyCategory(Enum):
    """Enumeration of property categories for organization and filtering."""
    PHYSICAL = "physical"
    CHEMICAL = "chemical"
    BIOLOGICAL = "biological"
    COMPUTATIONAL = "computational"
    EXPERIMENTAL = "experimental"

# Standard units for molecular properties
PROPERTY_UNITS = {
    "molecular_weight": "g/mol",
    "exact_mass": "g/mol",
    "logp": "",
    "tpsa": "Å²",
    "solubility": "mg/mL",
    "melting_point": "K",
    "boiling_point": "K",
    "pka": "",
    "pkb": "",
    "ic50": "nM",
    "ec50": "nM",
    "binding_affinity": "nM",
    "permeability": "cm/s",
    "clearance": "mL/min/kg",
    "half_life": "h",
    "bioavailability": "%",
    "volume_of_distribution": "L/kg"
}

# Valid ranges for molecular property values
PROPERTY_RANGES = {
    "molecular_weight": {"min": 0, "max": 2000},
    "exact_mass": {"min": 0, "max": 2000},
    "logp": {"min": -10, "max": 10},
    "tpsa": {"min": 0, "max": 500},
    "num_atoms": {"min": 1, "max": 1000},
    "num_heavy_atoms": {"min": 1, "max": 500},
    "num_rings": {"min": 0, "max": 50},
    "num_rotatable_bonds": {"min": 0, "max": 100},
    "num_h_donors": {"min": 0, "max": 50},
    "num_h_acceptors": {"min": 0, "max": 50},
    "solubility": {"min": 0, "max": 1000},
    "melting_point": {"min": 0, "max": 1000},
    "boiling_point": {"min": 0, "max": 1500},
    "pka": {"min": -10, "max": 20},
    "pkb": {"min": -10, "max": 20},
    "ic50": {"min": 0, "max": 1000000},
    "ec50": {"min": 0, "max": 1000000},
    "binding_affinity": {"min": 0, "max": 1000000},
    "permeability": {"min": 0, "max": 1},
    "clearance": {"min": 0, "max": 1000},
    "half_life": {"min": 0, "max": 100},
    "bioavailability": {"min": 0, "max": 100},
    "volume_of_distribution": {"min": 0, "max": 100}
}

# List of properties required for all molecules
REQUIRED_PROPERTIES = ["smiles", "inchi_key", "molecular_weight", "formula"]

# Comprehensive definitions of standard molecular properties
STANDARD_PROPERTIES = {
    "smiles": {
        "display_name": "SMILES",
        "property_type": PropertyType.STRING,
        "category": PropertyCategory.CHEMICAL,
        "description": "Simplified Molecular Input Line Entry System representation",
        "is_required": True,
        "is_filterable": True,
        "is_predictable": False
    },
    "inchi_key": {
        "display_name": "InChI Key",
        "property_type": PropertyType.STRING,
        "category": PropertyCategory.CHEMICAL,
        "description": "International Chemical Identifier Key",
        "is_required": True,
        "is_filterable": True,
        "is_predictable": False
    },
    "formula": {
        "display_name": "Molecular Formula",
        "property_type": PropertyType.STRING,
        "category": PropertyCategory.CHEMICAL,
        "description": "Chemical formula of the molecule",
        "is_required": True,
        "is_filterable": True,
        "is_predictable": False
    },
    "molecular_weight": {
        "display_name": "Molecular Weight",
        "property_type": PropertyType.NUMERIC,
        "category": PropertyCategory.PHYSICAL,
        "units": "g/mol",
        "description": "Average molecular mass of the molecule",
        "is_required": True,
        "is_filterable": True,
        "is_predictable": True
    },
    "exact_mass": {
        "display_name": "Exact Mass",
        "property_type": PropertyType.NUMERIC,
        "category": PropertyCategory.PHYSICAL,
        "units": "g/mol",
        "description": "Exact molecular mass of the molecule",
        "is_required": False,
        "is_filterable": True,
        "is_predictable": True
    },
    "logp": {
        "display_name": "LogP",
        "property_type": PropertyType.NUMERIC,
        "category": PropertyCategory.PHYSICAL,
        "description": "Octanol-water partition coefficient",
        "is_required": False,
        "is_filterable": True,
        "is_predictable": True
    },
    "tpsa": {
        "display_name": "TPSA",
        "property_type": PropertyType.NUMERIC,
        "category": PropertyCategory.PHYSICAL,
        "units": "Å²",
        "description": "Topological polar surface area",
        "is_required": False,
        "is_filterable": True,
        "is_predictable": True
    },
    "num_atoms": {
        "display_name": "Atom Count",
        "property_type": PropertyType.INTEGER,
        "category": PropertyCategory.PHYSICAL,
        "description": "Total number of atoms",
        "is_required": False,
        "is_filterable": True,
        "is_predictable": False
    },
    "num_heavy_atoms": {
        "display_name": "Heavy Atom Count",
        "property_type": PropertyType.INTEGER,
        "category": PropertyCategory.PHYSICAL,
        "description": "Number of non-hydrogen atoms",
        "is_required": False,
        "is_filterable": True,
        "is_predictable": False
    },
    "num_rings": {
        "display_name": "Ring Count",
        "property_type": PropertyType.INTEGER,
        "category": PropertyCategory.PHYSICAL,
        "description": "Number of rings in the molecule",
        "is_required": False,
        "is_filterable": True,
        "is_predictable": False
    },
    "num_rotatable_bonds": {
        "display_name": "Rotatable Bonds",
        "property_type": PropertyType.INTEGER,
        "category": PropertyCategory.PHYSICAL,
        "description": "Number of rotatable bonds",
        "is_required": False,
        "is_filterable": True,
        "is_predictable": True
    },
    "num_h_donors": {
        "display_name": "H-Bond Donors",
        "property_type": PropertyType.INTEGER,
        "category": PropertyCategory.PHYSICAL,
        "description": "Number of hydrogen bond donors",
        "is_required": False,
        "is_filterable": True,
        "is_predictable": True
    },
    "num_h_acceptors": {
        "display_name": "H-Bond Acceptors",
        "property_type": PropertyType.INTEGER,
        "category": PropertyCategory.PHYSICAL,
        "description": "Number of hydrogen bond acceptors",
        "is_required": False,
        "is_filterable": True,
        "is_predictable": True
    },
    "solubility": {
        "display_name": "Solubility",
        "property_type": PropertyType.NUMERIC,
        "category": PropertyCategory.PHYSICAL,
        "units": "mg/mL",
        "description": "Aqueous solubility",
        "is_required": False,
        "is_filterable": True,
        "is_predictable": True
    },
    "melting_point": {
        "display_name": "Melting Point",
        "property_type": PropertyType.NUMERIC,
        "category": PropertyCategory.PHYSICAL,
        "units": "K",
        "description": "Melting point temperature",
        "is_required": False,
        "is_filterable": True,
        "is_predictable": True
    },
    "boiling_point": {
        "display_name": "Boiling Point",
        "property_type": PropertyType.NUMERIC,
        "category": PropertyCategory.PHYSICAL,
        "units": "K",
        "description": "Boiling point temperature",
        "is_required": False,
        "is_filterable": True,
        "is_predictable": True
    },
    "pka": {
        "display_name": "pKa",
        "property_type": PropertyType.NUMERIC,
        "category": PropertyCategory.CHEMICAL,
        "description": "Acid dissociation constant",
        "is_required": False,
        "is_filterable": True,
        "is_predictable": True
    },
    "pkb": {
        "display_name": "pKb",
        "property_type": PropertyType.NUMERIC,
        "category": PropertyCategory.CHEMICAL,
        "description": "Base dissociation constant",
        "is_required": False,
        "is_filterable": True,
        "is_predictable": True
    },
    "ic50": {
        "display_name": "IC50",
        "property_type": PropertyType.NUMERIC,
        "category": PropertyCategory.BIOLOGICAL,
        "units": "nM",
        "description": "Half maximal inhibitory concentration",
        "is_required": False,
        "is_filterable": True,
        "is_predictable": True
    },
    "ec50": {
        "display_name": "EC50",
        "property_type": PropertyType.NUMERIC,
        "category": PropertyCategory.BIOLOGICAL,
        "units": "nM",
        "description": "Half maximal effective concentration",
        "is_required": False,
        "is_filterable": True,
        "is_predictable": True
    },
    "binding_affinity": {
        "display_name": "Binding Affinity",
        "property_type": PropertyType.NUMERIC,
        "category": PropertyCategory.BIOLOGICAL,
        "units": "nM",
        "description": "Binding affinity to target",
        "is_required": False,
        "is_filterable": True,
        "is_predictable": True
    },
    "permeability": {
        "display_name": "Permeability",
        "property_type": PropertyType.NUMERIC,
        "category": PropertyCategory.BIOLOGICAL,
        "units": "cm/s",
        "description": "Membrane permeability",
        "is_required": False,
        "is_filterable": True,
        "is_predictable": True
    },
    "clearance": {
        "display_name": "Clearance",
        "property_type": PropertyType.NUMERIC,
        "category": PropertyCategory.BIOLOGICAL,
        "units": "mL/min/kg",
        "description": "Rate of drug elimination",
        "is_required": False,
        "is_filterable": True,
        "is_predictable": True
    },
    "half_life": {
        "display_name": "Half-Life",
        "property_type": PropertyType.NUMERIC,
        "category": PropertyCategory.BIOLOGICAL,
        "units": "h",
        "description": "Time for concentration to reduce by half",
        "is_required": False,
        "is_filterable": True,
        "is_predictable": True
    },
    "bioavailability": {
        "display_name": "Bioavailability",
        "property_type": PropertyType.NUMERIC,
        "category": PropertyCategory.BIOLOGICAL,
        "units": "%",
        "description": "Fraction of drug that reaches systemic circulation",
        "is_required": False,
        "is_filterable": True,
        "is_predictable": True
    },
    "volume_of_distribution": {
        "display_name": "Volume of Distribution",
        "property_type": PropertyType.NUMERIC,
        "category": PropertyCategory.BIOLOGICAL,
        "units": "L/kg",
        "description": "Theoretical volume that would be required to contain the total amount of drug",
        "is_required": False,
        "is_filterable": True,
        "is_predictable": True
    },
    "lipinski_violations": {
        "display_name": "Lipinski Violations",
        "property_type": PropertyType.INTEGER,
        "category": PropertyCategory.COMPUTATIONAL,
        "description": "Number of Lipinski's Rule of Five violations",
        "is_required": False,
        "is_filterable": True,
        "is_predictable": True
    }
}

# List of properties that can be predicted by AI
PREDICTABLE_PROPERTIES = [
    "logp",
    "solubility",
    "permeability",
    "clearance",
    "half_life",
    "bioavailability",
    "ic50",
    "ec50",
    "binding_affinity",
    "pka",
    "pkb"
]

# List of properties that can be used for filtering molecules
FILTERABLE_PROPERTIES = [
    "molecular_weight",
    "logp",
    "tpsa",
    "num_rings",
    "num_rotatable_bonds",
    "num_h_donors",
    "num_h_acceptors",
    "solubility",
    "ic50",
    "ec50",
    "binding_affinity"
]