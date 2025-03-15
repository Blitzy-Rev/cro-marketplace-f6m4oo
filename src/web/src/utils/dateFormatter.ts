/**
 * dateFormatter.ts
 * 
 * Utility functions for formatting dates and timestamps consistently throughout the 
 * Molecular Data Management and CRO Integration Platform. Provides standardized date 
 * and time formatting for various UI components including submission lists, result displays,
 * and activity timelines.
 */

import { format, formatDistance, parseISO, isValid } from 'date-fns';
import { enUS } from 'date-fns/locale';
import { APP_CONFIG } from '../constants/appConfig';

// Default formatting constants
// These could potentially be overridden by UI configuration in the future
export const DEFAULT_DATE_FORMAT = 'MMM d, yyyy';
export const DEFAULT_TIME_FORMAT = 'h:mm a';
export const DEFAULT_DATETIME_FORMAT = 'MMM d, yyyy h:mm a';

/**
 * Formats a date string or Date object to a standardized date format
 * @param dateValue - Date to format (string, Date, null or undefined)
 * @param formatString - Optional format string (defaults to DEFAULT_DATE_FORMAT)
 * @returns Formatted date string or empty string if input is invalid
 */
export const formatDate = (
  dateValue: string | Date | null | undefined,
  formatString: string = DEFAULT_DATE_FORMAT
): string => {
  if (dateValue === null || dateValue === undefined || dateValue === '') {
    return '';
  }

  const date = typeof dateValue === 'string' ? parseISO(dateValue) : dateValue;
  
  if (!isValid(date)) {
    return '';
  }

  return format(date, formatString);
};

/**
 * Formats a date string or Date object to a standardized time format
 * @param dateValue - Date to format (string, Date, null or undefined)
 * @param formatString - Optional format string (defaults to DEFAULT_TIME_FORMAT)
 * @returns Formatted time string or empty string if input is invalid
 */
export const formatTime = (
  dateValue: string | Date | null | undefined,
  formatString: string = DEFAULT_TIME_FORMAT
): string => {
  if (dateValue === null || dateValue === undefined || dateValue === '') {
    return '';
  }

  const date = typeof dateValue === 'string' ? parseISO(dateValue) : dateValue;
  
  if (!isValid(date)) {
    return '';
  }

  return format(date, formatString);
};

/**
 * Formats a date string or Date object to a standardized date and time format
 * @param dateValue - Date to format (string, Date, null or undefined)
 * @param formatString - Optional format string (defaults to DEFAULT_DATETIME_FORMAT)
 * @returns Formatted date and time string or empty string if input is invalid
 */
export const formatDateTime = (
  dateValue: string | Date | null | undefined,
  formatString: string = DEFAULT_DATETIME_FORMAT
): string => {
  if (dateValue === null || dateValue === undefined || dateValue === '') {
    return '';
  }

  const date = typeof dateValue === 'string' ? parseISO(dateValue) : dateValue;
  
  if (!isValid(date)) {
    return '';
  }

  // Check for UI configuration preferences from APP_CONFIG if they exist in the future
  return format(date, formatString);
};

/**
 * Formats a date string or Date object as a relative time (e.g., '2 hours ago', '3 days ago')
 * @param dateValue - Date to format (string, Date, null or undefined)
 * @param baseDate - Optional base date to calculate relative time from (defaults to now)
 * @returns Relative time string or empty string if input is invalid
 */
export const formatRelativeTime = (
  dateValue: string | Date | null | undefined,
  baseDate: Date = new Date()
): string => {
  if (dateValue === null || dateValue === undefined || dateValue === '') {
    return '';
  }

  const date = typeof dateValue === 'string' ? parseISO(dateValue) : dateValue;
  
  if (!isValid(date)) {
    return '';
  }

  return formatDistance(date, baseDate, { 
    addSuffix: true,
    locale: enUS 
  });
};

/**
 * Formats a date for API requests in ISO format (YYYY-MM-DD)
 * @param dateValue - Date to format (string, Date, null or undefined)
 * @returns ISO formatted date string (YYYY-MM-DD) or empty string if input is invalid
 */
export const formatDateForAPI = (
  dateValue: Date | string | null | undefined
): string => {
  if (dateValue === null || dateValue === undefined || dateValue === '') {
    return '';
  }

  const date = typeof dateValue === 'string' ? parseISO(dateValue) : dateValue;
  
  if (!isValid(date)) {
    return '';
  }

  return format(date, 'yyyy-MM-dd');
};

/**
 * Checks if a date string or Date object is valid
 * @param dateValue - Date to check (string, Date, null or undefined)
 * @returns True if the date is valid, false otherwise
 */
export const isValidDate = (
  dateValue: string | Date | null | undefined
): boolean => {
  if (dateValue === null || dateValue === undefined || dateValue === '') {
    return false;
  }

  const date = typeof dateValue === 'string' ? parseISO(dateValue) : dateValue;
  return isValid(date);
};