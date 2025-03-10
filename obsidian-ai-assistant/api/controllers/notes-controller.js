/**
 * Notes Controller
 * 
 * Controller for CRUD operations on notes
 */

const AWS = require('aws-sdk');
const uuid = require('uuid');
const Note = require('../models/note');
const { ApiError } = require('../middleware/error-handler');
const { formatResponse } = require('../utils/response');

// Initialize AWS SDK clients
const dynamodb = new AWS.DynamoDB.DocumentClient();
const s3 = new AWS.S3();
const lambda = new AWS.Lambda();

// Environment variables
const TABLE_NAME = process.env.DYNAMODB_TABLE || 'ObsidianNotes';
const BUCKET_NAME = process.env.S3_BUCKET || 'obsidian-notes-bucket';
const EMBEDDINGS_FUNCTION = process.env.EMBEDDINGS_FUNCTION || 'obsidian-ai-assistant-embeddings';
const OPENSEARCH_DOMAIN = process.env.OPENSEARCH_DOMAIN || 'obsidian-search';

/**
 * List all notes
 * 
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {Function} next - Express next function
 */
async function listNotes(req, res, next) {
  try {
    const limit = parseInt(req.query.limit) || 50;
    const startKey = req.query.nextToken ? JSON.parse(Buffer.from(req.query.nextToken, 'base64').toString()) : null;
    
    const params = {
      TableName: TABLE_NAME,
      Limit: limit
    };
    
    if (startKey) {
      params.ExclusiveStartKey = startKey;
    }
    
    const result = await dynamodb.scan(params).promise();
    
    // Format response
    const response = {
      items: result.Items.map(item => new Note(item).toJSON())
    };
    
    // Add pagination token if there are more results
    if (result.LastEvaluatedKey) {
      response.nextToken = Buffer.from(JSON.stringify(result.LastEvaluatedKey)).toString('base64');
    }
    
    return res.status(200).json(response);
  } catch (error) {
    next(error);
  }
}

/**
 * Create a new note
 * 
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {Function} next - Express next function
 */
async function createNote(req, res, next) {
  try {
    const { title, content, tags = [] } = req.body;
    
    // Validate required fields
    if (!title) {
      throw new ApiError('VALIDATION_ERROR', 'Title is required', 400);
    }
    
    if (!content) {
      throw new ApiError('VALIDATION_ERROR', 'Content is required', 400);
    }
    
    // Generate a unique ID for the note
    const noteId = uuid.v4();
    const timestamp = Math.floor(Date.now() / 1000);
    const s3Key = `notes/${noteId}.md`;
    
    // Upload content to S3
    await s3.putObject({
      Bucket: BUCKET_NAME,
      Key: s3Key,
      Body: content,
      ContentType: 'text/markdown'
    }).promise();
    
    // Create note in DynamoDB
    const note = new Note({
      id: noteId,
      title,
      s3Key,
      createdAt: timestamp,
      updatedAt: timestamp,
      tags
    });
    
    await dynamodb.put({
      TableName: TABLE_NAME,
      Item: note.toDynamoDB()
    }).promise();
    
    // Generate embedding for the note (async)
    try {
      await lambda.invoke({
        FunctionName: EMBEDDINGS_FUNCTION,
        InvocationType: 'Event', // Async invocation
        Payload: JSON.stringify({
          action: 'index',
          noteId,
          content
        })
      }).promise();
    } catch (embeddingError) {
      console.error('Error generating embedding:', embeddingError);
      // Continue even if embedding fails
    }
    
    // Return the created note
    const noteWithContent = note.toJSON();
    noteWithContent.content = content;
    
    return res.status(201).json(noteWithContent);
  } catch (error) {
    next(error);
  }
}

/**
 * Get a note by ID
 * 
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {Function} next - Express next function
 */
async function getNoteById(req, res, next) {
  try {
    const noteId = req.params.id;
    
    // Get note metadata from DynamoDB
    const result = await dynamodb.get({
      TableName: TABLE_NAME,
      Key: { id: noteId }
    }).promise();
    
    if (!result.Item) {
      throw new ApiError('NOT_FOUND', `Note with ID ${noteId} not found`, 404);
    }
    
    const note = new Note(result.Item);
    
    // Get note content from S3
    const s3Result = await s3.getObject({
      Bucket: BUCKET_NAME,
      Key: note.s3Key
    }).promise();
    
    const content = s3Result.Body.toString('utf-8');
    
    // Return note with content
    const noteWithContent = note.toJSON();
    noteWithContent.content = content;
    
    return res.status(200).json(noteWithContent);
  } catch (error) {
    if (error.code === 'NoSuchKey') {
      return next(new ApiError('NOT_FOUND', `Note content not found in S3`, 404));
    }
    next(error);
  }
}

/**
 * Update a note
 * 
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {Function} next - Express next function
 */
async function updateNote(req, res, next) {
  try {
    const noteId = req.params.id;
    const { title, content, tags } = req.body;
    
    // Get existing note
    const result = await dynamodb.get({
      TableName: TABLE_NAME,
      Key: { id: noteId }
    }).promise();
    
    if (!result.Item) {
      throw new ApiError('NOT_FOUND', `Note with ID ${noteId} not found`, 404);
    }
    
    const note = new Note(result.Item);
    const timestamp = Math.floor(Date.now() / 1000);
    
    // Update note properties
    if (title) {
      note.title = title;
    }
    
    if (tags) {
      note.tags = tags;
    }
    
    note.updatedAt = timestamp;
    
    // Update content in S3 if provided
    if (content) {
      await s3.putObject({
        Bucket: BUCKET_NAME,
        Key: note.s3Key,
        Body: content,
        ContentType: 'text/markdown'
      }).promise();
      
      // Generate new embedding for the note (async)
      try {
        await lambda.invoke({
          FunctionName: EMBEDDINGS_FUNCTION,
          InvocationType: 'Event', // Async invocation
          Payload: JSON.stringify({
            action: 'index',
            noteId,
            content
          })
        }).promise();
      } catch (embeddingError) {
        console.error('Error generating embedding:', embeddingError);
        // Continue even if embedding fails
      }
    }
    
    // Update note in DynamoDB
    await dynamodb.update({
      TableName: TABLE_NAME,
      Key: { id: noteId },
      UpdateExpression: 'SET title = :title, updatedAt = :updatedAt, tags = :tags',
      ExpressionAttributeValues: {
        ':title': note.title,
        ':updatedAt': note.updatedAt,
        ':tags': note.tags
      }
    }).promise();
    
    // Get updated content from S3
    const s3Result = await s3.getObject({
      Bucket: BUCKET_NAME,
      Key: note.s3Key
    }).promise();
    
    const updatedContent = s3Result.Body.toString('utf-8');
    
    // Return updated note with content
    const noteWithContent = note.toJSON();
    noteWithContent.content = updatedContent;
    
    return res.status(200).json(noteWithContent);
  } catch (error) {
    next(error);
  }
}

/**
 * Delete a note
 * 
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {Function} next - Express next function
 */
async function deleteNote(req, res, next) {
  try {
    const noteId = req.params.id;
    
    // Get note to get the S3 key
    const result = await dynamodb.get({
      TableName: TABLE_NAME,
      Key: { id: noteId }
    }).promise();
    
    if (!result.Item) {
      throw new ApiError('NOT_FOUND', `Note with ID ${noteId} not found`, 404);
    }
    
    const note = new Note(result.Item);
    
    // Delete note from DynamoDB
    await dynamodb.delete({
      TableName: TABLE_NAME,
      Key: { id: noteId }
    }).promise();
    
    // Delete note content from S3
    await s3.deleteObject({
      Bucket: BUCKET_NAME,
      Key: note.s3Key
    }).promise();
    
    // Delete note from OpenSearch (async)
    try {
      await lambda.invoke({
        FunctionName: EMBEDDINGS_FUNCTION,
        InvocationType: 'Event', // Async invocation
        Payload: JSON.stringify({
          action: 'delete',
          noteId
        })
      }).promise();
    } catch (embeddingError) {
      console.error('Error deleting from OpenSearch:', embeddingError);
      // Continue even if OpenSearch deletion fails
    }
    
    return res.status(204).send();
  } catch (error) {
    next(error);
  }
}

/**
 * Search notes
 * 
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {Function} next - Express next function
 */
async function searchNotes(req, res, next) {
  try {
    const query = req.query.q;
    const semantic = req.query.semantic !== 'false'; // Default to true
    const limit = parseInt(req.query.limit) || 10;
    
    if (!query) {
      throw new ApiError('VALIDATION_ERROR', 'Search query is required', 400);
    }
    
    let results;
    
    if (semantic) {
      // Semantic search using embeddings
      try {
        // Generate embedding for the query
        const embeddingResult = await lambda.invoke({
          FunctionName: EMBEDDINGS_FUNCTION,
          InvocationType: 'RequestResponse',
          Payload: JSON.stringify({
            action: 'embed',
            text: query
          })
        }).promise();
        
        const embeddingPayload = JSON.parse(embeddingResult.Payload);
        
        if (!embeddingPayload.embedding) {
          throw new Error('Failed to generate embedding for search query');
        }
        
        // Search OpenSearch using the embedding
        const searchResult = await lambda.invoke({
          FunctionName: EMBEDDINGS_FUNCTION,
          InvocationType: 'RequestResponse',
          Payload: JSON.stringify({
            action: 'search',
            embedding: embeddingPayload.embedding,
            limit
          })
        }).promise();
        
        const searchPayload = JSON.parse(searchResult.Payload);
        
        if (!searchPayload.results) {
          throw new Error('Failed to search with embedding');
        }
        
        // Get full note details for each result
        results = await Promise.all(
          searchPayload.results.map(async (result) => {
            try {
              // Get note metadata from DynamoDB
              const noteResult = await dynamodb.get({
                TableName: TABLE_NAME,
                Key: { id: result.id }
              }).promise();
              
              if (!noteResult.Item) {
                return null;
              }
              
              const note = new Note(noteResult.Item);
              
              // Get note content from S3
              const s3Result = await s3.getObject({
                Bucket: BUCKET_NAME,
                Key: note.s3Key
              }).promise();
              
              const content = s3Result.Body.toString('utf-8');
              
              // Return note with content
              const noteWithContent = note.toJSON();
              noteWithContent.content = content;
              noteWithContent.score = result.score;
              
              return noteWithContent;
            } catch (error) {
              console.error(`Error getting note ${result.id}:`, error);
              return null;
            }
          })
        );
        
        // Filter out null results
        results = results.filter(Boolean);
      } catch (error) {
        console.error('Error performing semantic search:', error);
        
        // Fall back to text search
        results = await performTextSearch(query, limit);
      }
    } else {
      // Text search
      results = await performTextSearch(query, limit);
    }
    
    return res.status(200).json(results);
  } catch (error) {
    next(error);
  }
}

/**
 * Perform text-based search on notes
 * 
 * @param {string} query - Search query
 * @param {number} limit - Maximum number of results
 * @returns {Promise<Array>} - Search results
 */
async function performTextSearch(query, limit) {
  // Scan DynamoDB for notes matching the query
  const scanParams = {
    TableName: TABLE_NAME,
    FilterExpression: 'contains(#title, :query)',
    ExpressionAttributeNames: {
      '#title': 'title'
    },
    ExpressionAttributeValues: {
      ':query': query
    }
  };
  
  const scanResult = await dynamodb.scan(scanParams).promise();
  
  // Get content for each note and check for matches
  const results = await Promise.all(
    scanResult.Items.map(async (item) => {
      try {
        const note = new Note(item);
        
        // Get note content from S3
        const s3Result = await s3.getObject({
          Bucket: BUCKET_NAME,
          Key: note.s3Key
        }).promise();
        
        const content = s3Result.Body.toString('utf-8');
        
        // Check if content contains the query
        if (content.toLowerCase().includes(query.toLowerCase())) {
          const noteWithContent = note.toJSON();
          noteWithContent.content = content;
          return noteWithContent;
        }
        
        return null;
      } catch (error) {
        console.error(`Error getting note ${item.id}:`, error);
        return null;
      }
    })
  );
  
  // Filter out null results and limit
  return results.filter(Boolean).slice(0, limit);
}

module.exports = {
  listNotes,
  createNote,
  getNoteById,
  updateNote,
  deleteNote,
  searchNotes
}; 