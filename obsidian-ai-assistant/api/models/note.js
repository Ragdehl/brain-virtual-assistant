/**
 * Note Model
 * 
 * Represents a note in the system
 */

/**
 * Note class
 */
class Note {
  /**
   * Create a new Note instance
   * 
   * @param {Object} data - Note data
   */
  constructor(data = {}) {
    this.id = data.id || '';
    this.title = data.title || '';
    this.s3Key = data.s3Key || '';
    this.createdAt = data.createdAt || 0;
    this.updatedAt = data.updatedAt || 0;
    this.tags = data.tags || [];
  }
  
  /**
   * Convert the note to a JSON object
   * 
   * @returns {Object} - JSON representation of the note
   */
  toJSON() {
    return {
      id: this.id,
      title: this.title,
      createdAt: this.createdAt,
      updatedAt: this.updatedAt,
      tags: this.tags
    };
  }
  
  /**
   * Convert the note to a DynamoDB item
   * 
   * @returns {Object} - DynamoDB representation of the note
   */
  toDynamoDB() {
    return {
      id: this.id,
      title: this.title,
      s3Key: this.s3Key,
      createdAt: this.createdAt,
      updatedAt: this.updatedAt,
      tags: this.tags
    };
  }
  
  /**
   * Create a Note instance from a DynamoDB item
   * 
   * @param {Object} item - DynamoDB item
   * @returns {Note} - Note instance
   */
  static fromDynamoDB(item) {
    return new Note({
      id: item.id,
      title: item.title,
      s3Key: item.s3Key,
      createdAt: item.createdAt,
      updatedAt: item.updatedAt,
      tags: item.tags || []
    });
  }
}

module.exports = Note; 