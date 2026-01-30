# Backlog

This backlog is organized into lots (L2..L8). Each lot includes goal, scope, dependencies, definition of done, risks, and sizing in 1–3 day increments.

## L2 — Project Baseline & Architecture
- **Goal:** Establish a clear project baseline, structure, and architectural direction for the CRM.
- **Scope:**
  - Define core domains (Accounts, Contacts, Deals, Activities).
  - Create high-level service boundaries/modules.
  - Document initial data model and API boundaries.
- **Dependencies:** None.
- **Definition of Done:**
  - Architecture notes documented.
  - Initial module layout agreed and committed.
  - Data model sketch checked into repo.
- **Risks:** Ambiguous requirements may cause rework later.
- **Sizing:** 2 days.

## L3 — Data Layer & Migrations
- **Goal:** Establish database schema and migration workflow.
- **Scope:**
  - Define tables for core entities.
  - Add migration tooling and base migration scripts.
  - Seed minimal test data.
- **Dependencies:** L2.
- **Definition of Done:**
  - Migrations run cleanly on fresh database.
  - Schema includes Accounts, Contacts, Deals, Activities.
  - Seed data loads without errors.
- **Risks:** Schema changes likely as requirements solidify.
- **Sizing:** 3 days.

## L4 — Core API (Accounts & Contacts)
- **Goal:** Provide CRUD APIs for Accounts and Contacts.
- **Scope:**
  - REST endpoints for Accounts and Contacts.
  - Validation and basic error handling.
  - Basic pagination and filtering.
- **Dependencies:** L3.
- **Definition of Done:**
  - CRUD endpoints documented and tested.
  - Pagination/filtering works for list endpoints.
  - Error responses consistent.
- **Risks:** API contract changes if UI needs differ.
- **Sizing:** 3 days.

## L5 — Deals & Activities API
- **Goal:** Deliver API support for Deals and Activities.
- **Scope:**
  - CRUD for Deals and Activities.
  - Basic workflow fields (stage, status, due date).
  - Relationship enforcement (Deal → Account, Activity → Contact/Deal).
- **Dependencies:** L3.
- **Definition of Done:**
  - CRUD endpoints for Deals/Activities working.
  - Relationship integrity enforced.
  - Tests cover main flows.
- **Risks:** Workflow details may expand scope.
- **Sizing:** 3 days.

## L6 — Authentication & Authorization
- **Goal:** Secure the CRM with basic auth and role checks.
- **Scope:**
  - User model and credential storage.
  - Session or token auth.
  - Role-based access rules for key endpoints.
- **Dependencies:** L4.
- **Definition of Done:**
  - Auth required for protected endpoints.
  - Roles enforced for create/update/delete.
  - Basic auth tests pass.
- **Risks:** Security design might need expansion later.
- **Sizing:** 2 days.

## L7 — Frontend MVP
- **Goal:** Provide a minimal UI to manage core entities.
- **Scope:**
  - List and detail views for Accounts, Contacts, Deals.
  - Create/edit forms.
  - Basic navigation.
- **Dependencies:** L4, L5.
- **Definition of Done:**
  - UI can create and edit core entities.
  - Lists load data with pagination.
  - Error states and empty states handled.
- **Risks:** UI scope creep if workflows expand.
- **Sizing:** 3 days.

## L8 — Reporting & Export
- **Goal:** Provide basic reporting and export capability.
- **Scope:**
  - Simple pipeline report (Deals by stage).
  - Activity report by user/date.
  - CSV export for Accounts and Deals.
- **Dependencies:** L5.
- **Definition of Done:**
  - Reports load with realistic data.
  - CSV exports available from UI or API.
  - Basic performance sanity checks done.
- **Risks:** Reporting requirements could expand quickly.
- **Sizing:** 2 days.
