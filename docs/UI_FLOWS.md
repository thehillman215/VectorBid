---

### `docs/UI_FLOWS.md`
```markdown
# UI Flows

## Onboarding
- Pilot enters profile (name, airline, seniority, seat, base).
- Stored in database for reuse.

## Monthly Workflow
1. **Upload Bid Package** - New upload step with file parsing
   - Navigate to `/upload` page
   - Select bid package file (PDF, CSV, TXT, JSONL)
   - Fill in metadata: airline, month, base, fleet, seat, pilot_id
   - System parses file and returns summary: trips, legs, date_span, credit_total
   - File stored with hash-based ID for future reference
2. Upload bid package (admin or pilot).
3. Confirm packet matches profile.
4. Select or customize **Persona** (default strategies).
5. Enter natural language preferences or adjust sliders.
6. Review top-K candidate schedules and rationales.
7. Copy/export PBS-ready bid layers.

## Upload Flow Details
- **File Support**: PDF (United Airlines format), CSV (pairings/trips), TXT, JSONL
- **Validation**: File format detection, required field validation, size limits
- **Parsing**: Integration with existing PBS parser for structured formats
- **Storage**: File-backed storage with SQLite metadata tracking
- **UI**: HTMX-powered form with real-time feedback and error handling

## Personas
- "Quality of Life": maximize weekends off.
- "Max Credit": maximize pay hours.
- "Commutable": avoid back-to-back trips.