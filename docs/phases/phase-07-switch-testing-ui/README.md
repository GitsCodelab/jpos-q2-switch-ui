# Phase 07 - Switch Testing UI

## Overview
Provides operational UI page to send ISO8583 test transactions into the jPOS switch.

## Goals
- Trigger single transaction tests from UI for testing end to end process
- Display switch response
- Support operational QA testing

## Status
Operational


## Current Capabilities

- Send ISO8583 test transactions from UI
- Select predefined transaction profiles
- Override ISO fields manually
- View switch response and response codes
- Connect directly from backend to the jPOS switch over TCP at `switch:9000`
- Keep recent request/response history in backend memory for UI restore and review
- Restore request fields from recent history entries
- Show operator-facing validation and switch connectivity errors

## MVP Implementation State

- Backend endpoints are available under `/api/v1/testing`
- Authentication is required for profiles, send, and history endpoints
- Backend sends ISO8583 requests directly to the switch using jPOS `ASCIIChannel` framing
- Frontend page is available from the main navigation as `Switch Testing`
- Profiles implemented: `atm`, `pos`, `reversal`, `fraud`, `custom`
- Recent history is in-memory only and is cleared when the backend restarts

## Verified MVP Checks

- Backend tests for profiles, send, validation, history, and switch-unreachable handling pass
- Live `POST /api/v1/testing/send` returns `200 OK` against the running switch
- Live `GET /api/v1/testing/history` returns the recent sent transaction
- Frontend production build passes with the Switch Testing page included

## Not In MVP

- PostgreSQL persistence for switch-testing history
- Dedicated testing schemas file for request/response models
- Full browser-automated end-to-end test coverage
- Refactoring `single_iso_simulator.py` into the active backend integration path