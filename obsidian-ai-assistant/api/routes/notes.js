/**
 * Notes API Routes
 * 
 * Routes for CRUD operations on notes
 */

const express = require('express');
const router = express.Router();
const notesController = require('../controllers/notes-controller');

/**
 * @route GET /notes
 * @description Get all notes
 * @access Private
 */
router.get('/', notesController.listNotes);

/**
 * @route POST /notes
 * @description Create a new note
 * @access Private
 */
router.post('/', notesController.createNote);

/**
 * @route GET /notes/search
 * @description Search notes
 * @access Private
 */
router.get('/search', notesController.searchNotes);

/**
 * @route GET /notes/:id
 * @description Get a note by ID
 * @access Private
 */
router.get('/:id', notesController.getNoteById);

/**
 * @route PUT /notes/:id
 * @description Update a note
 * @access Private
 */
router.put('/:id', notesController.updateNote);

/**
 * @route DELETE /notes/:id
 * @description Delete a note
 * @access Private
 */
router.delete('/:id', notesController.deleteNote);

module.exports = router; 