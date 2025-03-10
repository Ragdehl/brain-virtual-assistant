/**
 * Response Utilities
 * 
 * Utilities for formatting API responses
 */

/**
 * Format a successful response
 * 
 * @param {any} data - Response data
 * @param {number} statusCode - HTTP status code
 * @returns {Object} - Formatted response
 */
function formatResponse(data, statusCode = 200) {
  return {
    statusCode,
    body: JSON.stringify(data),
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Credentials': true
    }
  };
}

/**
 * Format an error response
 * 
 * @param {Error} error - Error object
 * @param {number} statusCode - HTTP status code
 * @returns {Object} - Formatted error response
 */
function formatError(error, statusCode = 500) {
  const errorResponse = {
    code: error.code || 'INTERNAL_SERVER_ERROR',
    message: error.message || 'An unexpected error occurred'
  };
  
  if (error.details && process.env.NODE_ENV !== 'production') {
    errorResponse.details = error.details;
  }
  
  return {
    statusCode,
    body: JSON.stringify(errorResponse),
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Credentials': true
    }
  };
}

/**
 * Format a validation error response
 * 
 * @param {string} message - Error message
 * @param {Object} details - Validation error details
 * @returns {Object} - Formatted validation error response
 */
function formatValidationError(message, details) {
  return formatError(
    {
      code: 'VALIDATION_ERROR',
      message: message || 'Validation failed',
      details
    },
    400
  );
}

/**
 * Format a not found error response
 * 
 * @param {string} message - Error message
 * @returns {Object} - Formatted not found error response
 */
function formatNotFoundError(message) {
  return formatError(
    {
      code: 'NOT_FOUND',
      message: message || 'Resource not found'
    },
    404
  );
}

module.exports = {
  formatResponse,
  formatError,
  formatValidationError,
  formatNotFoundError
}; 