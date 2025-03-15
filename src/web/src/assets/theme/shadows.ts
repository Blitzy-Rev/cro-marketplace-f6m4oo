/**
 * Shadow elevation system for the Molecular Data Management and CRO Integration Platform
 * Implements Material Design elevation with 5 primary levels of shadow depth
 * for component hierarchy and consistent interface layering.
 * 
 * Shadows increase in intensity with elevation to provide visual cues about
 * component relationships and importance in the interface.
 * 
 * @version 1.0.0
 */

/**
 * Creates a CSS shadow string with proper rgba formatting and consistent structure
 * 
 * @param px1 - Horizontal offset in pixels
 * @param px2 - Vertical offset in pixels
 * @param px3 - Blur radius in pixels
 * @param px4 - Spread radius in pixels
 * @param alpha - Shadow opacity (0-1)
 * @returns Formatted CSS shadow value
 */
const createShadow = (px1: number, px2: number, px3: number, px4: number, alpha: number): string => {
  return `${px1}px ${px2}px ${px3}px ${px4}px rgba(0, 0, 0, ${alpha})`;
};

// Array of shadow definitions with increasing elevation levels
// From 0 (no shadow) to 24 (maximum elevation)
const shadows = [
  'none', // 0 - No shadow
  // Level 1 - Low elevation (cards, buttons)
  `${createShadow(0, 2, 1, -1, 0.2)},${createShadow(0, 1, 1, 0, 0.14)},${createShadow(0, 1, 3, 0, 0.12)}`,
  // Level 2 - Low-medium elevation (dropdown menus, molecule cards)
  `${createShadow(0, 3, 1, -2, 0.2)},${createShadow(0, 2, 2, 0, 0.14)},${createShadow(0, 1, 5, 0, 0.12)}`,
  // Level 3 - Medium elevation (navigation drawers, molecule detail panels)
  `${createShadow(0, 3, 3, -2, 0.2)},${createShadow(0, 3, 4, 0, 0.14)},${createShadow(0, 1, 8, 0, 0.12)}`,
  // Level 4 - Medium-high elevation (dialogs, property panels)
  `${createShadow(0, 2, 4, -1, 0.2)},${createShadow(0, 4, 5, 0, 0.14)},${createShadow(0, 1, 10, 0, 0.12)}`,
  // Level 5 - High elevation (modals, CRO submission interface)
  `${createShadow(0, 3, 5, -1, 0.2)},${createShadow(0, 5, 8, 0, 0.14)},${createShadow(0, 1, 14, 0, 0.12)}`,
  // Additional elevation levels for specialized UI components
  `${createShadow(0, 3, 5, -1, 0.2)},${createShadow(0, 6, 10, 0, 0.14)},${createShadow(0, 1, 18, 0, 0.12)}`,
  `${createShadow(0, 4, 5, -2, 0.2)},${createShadow(0, 7, 10, 1, 0.14)},${createShadow(0, 2, 16, 1, 0.12)}`,
  `${createShadow(0, 5, 5, -3, 0.2)},${createShadow(0, 8, 10, 1, 0.14)},${createShadow(0, 3, 14, 2, 0.12)}`,
  `${createShadow(0, 5, 6, -3, 0.2)},${createShadow(0, 9, 12, 1, 0.14)},${createShadow(0, 3, 16, 2, 0.12)}`,
  `${createShadow(0, 6, 6, -3, 0.2)},${createShadow(0, 10, 14, 1, 0.14)},${createShadow(0, 4, 18, 3, 0.12)}`,
  `${createShadow(0, 6, 7, -4, 0.2)},${createShadow(0, 11, 15, 1, 0.14)},${createShadow(0, 4, 20, 3, 0.12)}`,
  `${createShadow(0, 7, 8, -4, 0.2)},${createShadow(0, 12, 17, 2, 0.14)},${createShadow(0, 5, 22, 4, 0.12)}`,
  `${createShadow(0, 7, 8, -4, 0.2)},${createShadow(0, 13, 19, 2, 0.14)},${createShadow(0, 5, 24, 4, 0.12)}`,
  `${createShadow(0, 7, 9, -4, 0.2)},${createShadow(0, 14, 21, 2, 0.14)},${createShadow(0, 5, 26, 4, 0.12)}`,
  `${createShadow(0, 8, 9, -5, 0.2)},${createShadow(0, 15, 22, 2, 0.14)},${createShadow(0, 6, 28, 5, 0.12)}`,
  `${createShadow(0, 8, 10, -5, 0.2)},${createShadow(0, 16, 24, 2, 0.14)},${createShadow(0, 6, 30, 5, 0.12)}`,
  `${createShadow(0, 8, 11, -5, 0.2)},${createShadow(0, 17, 26, 2, 0.14)},${createShadow(0, 6, 32, 5, 0.12)}`,
  `${createShadow(0, 9, 11, -5, 0.2)},${createShadow(0, 18, 28, 2, 0.14)},${createShadow(0, 7, 34, 6, 0.12)}`,
  `${createShadow(0, 9, 12, -6, 0.2)},${createShadow(0, 19, 29, 2, 0.14)},${createShadow(0, 7, 36, 6, 0.12)}`,
  `${createShadow(0, 10, 13, -6, 0.2)},${createShadow(0, 20, 31, 3, 0.14)},${createShadow(0, 8, 38, 7, 0.12)}`,
  `${createShadow(0, 10, 13, -6, 0.2)},${createShadow(0, 21, 33, 3, 0.14)},${createShadow(0, 8, 40, 7, 0.12)}`,
  `${createShadow(0, 10, 14, -6, 0.2)},${createShadow(0, 22, 35, 3, 0.14)},${createShadow(0, 8, 42, 7, 0.12)}`,
  `${createShadow(0, 11, 14, -7, 0.2)},${createShadow(0, 23, 36, 3, 0.14)},${createShadow(0, 9, 44, 8, 0.12)}`,
  `${createShadow(0, 11, 15, -7, 0.2)},${createShadow(0, 24, 38, 3, 0.14)},${createShadow(0, 9, 46, 8, 0.12)}`,
];

export default shadows;