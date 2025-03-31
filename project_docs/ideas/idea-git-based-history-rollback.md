---
title: "Git-based history and rollback in the assistant"
status: considering
created: 2025-03-29
updated: 2025-03-29
confidence: medium
origin: assistant
related_to: [versioning, UX]
tags: [idea, feature]
---

## Summary

Allow users to see past versions of a note and restore previous states using Git commits.

## Context

Discussed while setting up the Git + S3 flow.

## Benefits

- [x] Clean undo mechanism
- [x] Explains why things changed
- [ ] Could build trust in the assistant

## Potential Next Steps

- [ ] Build diff UI or markdown preview
- [ ] Add commit viewer in the assistant
- [ ] Optional rollback command

## Notes

Would pair well with metadata like `status: restored_from_commit`.
