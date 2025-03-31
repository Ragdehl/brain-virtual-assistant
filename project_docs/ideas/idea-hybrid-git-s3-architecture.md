---
title: "Hybrid Git + S3 architecture"
status: in progress
created: 2025-03-29
updated: 2025-03-29
confidence: high
origin: assistant
related_to: [note storage, user sync, git backend]
tags: [idea, architecture, sync]
---

## Summary

Use Git locally on the backend for versioning, and sync notes to S3 for private, scalable user storage. Gives full control over data and integrates well with Obsidian.

## Context

Came up while comparing GitHub vs S3 for storing user notes.

## Benefits

- [x] Git-level version control
- [x] User data stays private in S3
- [x] Compatible with Obsidian
- [ ] Git-independent deployments

## Potential Next Steps

- [x] Prototype create/update/restore flow
- [ ] Add change history UI
- [ ] Set up S3 access per user

## Notes

Ideal for privacy-conscious users.
