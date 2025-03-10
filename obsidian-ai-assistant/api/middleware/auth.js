/**
 * Authentication Middleware
 * 
 * Validates API keys for protected routes
 */

const AWS = require('aws-sdk');
const ssm = new AWS.SSM();

// Cache for API keys to reduce SSM calls
const apiKeyCache = new Map();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

/**
 * Validates the API key from the request header
 * 
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {Function} next - Express next function
 */
async function authMiddleware(req, res, next) {
  try {
    const apiKey = req.header('x-api-key');
    
    // Check if API key is provided
    if (!apiKey) {
      return res.status(401).json({
        code: 'UNAUTHORIZED',
        message: 'API key is required'
      });
    }
    
    // Validate API key
    const isValid = await validateApiKey(apiKey);
    
    if (!isValid) {
      return res.status(401).json({
        code: 'UNAUTHORIZED',
        message: 'Invalid API key'
      });
    }
    
    // API key is valid, proceed to the next middleware
    next();
  } catch (error) {
    console.error('Authentication error:', error);
    return res.status(500).json({
      code: 'INTERNAL_SERVER_ERROR',
      message: 'An error occurred during authentication'
    });
  }
}

/**
 * Validates the API key against stored keys in SSM Parameter Store
 * 
 * @param {string} apiKey - The API key to validate
 * @returns {Promise<boolean>} - Whether the API key is valid
 */
async function validateApiKey(apiKey) {
  try {
    // Check cache first
    if (apiKeyCache.has(apiKey)) {
      const { isValid, timestamp } = apiKeyCache.get(apiKey);
      
      // Check if cache entry is still valid
      if (Date.now() - timestamp < CACHE_TTL) {
        return isValid;
      }
      
      // Cache entry expired, remove it
      apiKeyCache.delete(apiKey);
    }
    
    // Get API keys from SSM Parameter Store
    const parameterName = process.env.API_KEYS_PARAMETER || '/obsidian-ai-assistant/api-keys';
    const response = await ssm.getParameter({
      Name: parameterName,
      WithDecryption: true
    }).promise();
    
    // Parse API keys from parameter value (comma-separated list)
    const validApiKeys = response.Parameter.Value.split(',').map(key => key.trim());
    
    // Check if provided API key is in the list
    const isValid = validApiKeys.includes(apiKey);
    
    // Cache the result
    apiKeyCache.set(apiKey, {
      isValid,
      timestamp: Date.now()
    });
    
    return isValid;
  } catch (error) {
    console.error('Error validating API key:', error);
    
    // In case of error, default to invalid
    return false;
  }
}

module.exports = authMiddleware; 