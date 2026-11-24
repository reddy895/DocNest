/**
 * Shared frontend domain types (JSDoc) used across the DocNest application.
 */

/**
 * @typedef {Object} Conversation
 * @property {string} id
 * @property {string} user_id
 * @property {string} workspace_id
 * @property {string} title
 * @property {boolean} is_pinned
 * @property {string} created_at
 * @property {string} updated_at
 * @property {number} message_count
 */

/**
 * @typedef {Object} Citation
 * @property {string} source_id
 * @property {string} filename
 * @property {number} page_number
 * @property {number} chunk_index
 * @property {string} content
 * @property {number} relevance_score
 */

/**
 * @typedef {Object} ChatMessage
 * @property {string} id
 * @property {'user'|'assistant'|'system'} sender
 * @property {string} text
 * @property {Citation[]} [citations]
 * @property {Object} [trace]
 * @property {number|null} [feedback_rating]
 * @property {string} [timestamp]
 */

/**
 * @typedef {Object} DocumentInfo
 * @property {string} doc_id
 * @property {string} filename
 * @property {number} page_count
 * @property {number} total_chunks
 * @property {string} status
 * @property {string[]} tags
 */

export {};
