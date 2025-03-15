import { Components } from '@mui/material/styles'; // @mui/material/styles ^5.0.0
import { primary, secondary, error, grey } from './palette';

/**
 * Custom component style overrides for the Material UI theme used in the
 * Molecular Data Management and CRO Integration Platform.
 * 
 * These style overrides ensure consistent appearance and behavior across
 * the application, implementing the design system specifications.
 */
export const components: Components = {
  MuiButton: {
    styleOverrides: {
      root: {
        borderRadius: '8px',
        textTransform: 'none', // Prevents all-caps text
        fontWeight: 500,
        boxShadow: 'none',
        '&:hover': {
          boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.1)'
        }
      },
      contained: {
        boxShadow: '0px 1px 2px rgba(0, 0, 0, 0.05)'
      },
      containedPrimary: {
        backgroundColor: '#1976d2',
        '&:hover': {
          backgroundColor: '#1565c0'
        }
      },
      containedSecondary: {
        backgroundColor: '#388e3c',
        '&:hover': {
          backgroundColor: '#2e7d32'
        }
      },
      outlined: {
        borderWidth: '1px'
      },
      sizeSmall: {
        padding: '6px 16px'
      },
      sizeMedium: {
        padding: '8px 20px'
      },
      sizeLarge: {
        padding: '10px 24px'
      }
    },
    defaultProps: {
      disableElevation: true
    }
  },
  
  MuiTextField: {
    styleOverrides: {
      root: {
        marginBottom: '16px'
      }
    },
    defaultProps: {
      variant: 'outlined',
      size: 'medium',
      fullWidth: true
    }
  },
  
  MuiCard: {
    styleOverrides: {
      root: {
        borderRadius: '12px',
        boxShadow: '0px 2px 8px rgba(0, 0, 0, 0.08)',
        overflow: 'visible'
      }
    }
  },
  
  MuiTable: {
    styleOverrides: {
      root: {
        tableLayout: 'fixed'
      }
    }
  },
  
  MuiTableCell: {
    styleOverrides: {
      root: {
        padding: '12px 16px',
        borderBottom: '1px solid rgba(0, 0, 0, 0.08)'
      },
      head: {
        fontWeight: 600,
        color: 'rgba(0, 0, 0, 0.87)',
        backgroundColor: '#f5f5f5'
      }
    }
  },
  
  MuiTableHead: {
    styleOverrides: {
      root: {
        backgroundColor: '#f5f5f5'
      }
    }
  },
  
  MuiTab: {
    styleOverrides: {
      root: {
        textTransform: 'none',
        fontWeight: 500,
        minWidth: '100px'
      }
    }
  },
  
  MuiTabs: {
    styleOverrides: {
      indicator: {
        height: '3px',
        borderRadius: '3px 3px 0 0'
      }
    }
  },
  
  MuiChip: {
    styleOverrides: {
      root: {
        borderRadius: '16px',
        height: '32px'
      },
      label: {
        fontWeight: 500,
        padding: '0 12px'
      }
    }
  },
  
  MuiDialog: {
    styleOverrides: {
      paper: {
        borderRadius: '12px',
        boxShadow: '0px 8px 24px rgba(0, 0, 0, 0.15)'
      }
    }
  },
  
  MuiPaper: {
    styleOverrides: {
      rounded: {
        borderRadius: '12px'
      },
      elevation1: {
        boxShadow: '0px 2px 8px rgba(0, 0, 0, 0.08)'
      }
    }
  },
  
  MuiAppBar: {
    styleOverrides: {
      root: {
        boxShadow: '0px 1px 4px rgba(0, 0, 0, 0.1)'
      }
    },
    defaultProps: {
      color: 'primary',
      elevation: 0
    }
  },
  
  MuiDrawer: {
    styleOverrides: {
      paper: {
        borderRight: '1px solid rgba(0, 0, 0, 0.08)'
      }
    }
  },
  
  MuiSlider: {
    styleOverrides: {
      root: {
        height: 8
      },
      thumb: {
        height: 20,
        width: 20
      },
      track: {
        height: 8,
        borderRadius: 4
      },
      rail: {
        height: 8,
        borderRadius: 4
      }
    }
  },
  
  MuiTooltip: {
    styleOverrides: {
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        padding: '8px 12px',
        fontSize: '0.75rem'
      }
    }
  }
};