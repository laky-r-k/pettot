# PetTot owner website — flow and interaction map

## Primary route

**Welcome → Pet setup → Overview → Daily check-in → Review / contact**

### 1. Welcome / demo entry
- Make it obvious this is a prototype.
- Do not request a password or imply that an account was created.
- Entering the demo opens setup for a new user or the saved local profile's overview.

### 2. Pet and procedure setup
- Required: pet name, species, procedure name, procedure date.
- Optional: breed, clinic, veterinarian/contact, phone/email, discharge instructions.
- Store only in local browser storage; this is not server-side storage or a protected account.

### 3. Overview
- Lead with one primary task: today's check-in.
- Keep the secondary tasks visible but quiet: photo comparison, medication log and clinic contacts.
- Display only recent locally stored notes and the last image-model result summary.

### 4. Daily check-in
- Ask about comfort, appetite, movement, visible incision changes and the medication plan.
- Provide explicit warning-sign selections, separate from AI model logic.
- Save the entry with local date/time; if a serious sign is selected, tell the owner to seek veterinary help rather than waiting for photo analysis.
- Check-ins are owner observations and are not scored as diagnoses.

### 5. Photo review
- Test the API connection before asking the user to upload.
- Face analysis uses the current API's `file`, `baseline_mar` and `force_fallback` fields.
- Incision comparison requires both `day1_file` and `dayN_file`.
- Present statuses as prototype-model flags; show limitations beside every result. Never display “vet notified.”
- A photo is sent only when the owner submits the analysis form.

### 6. Care and contacts
- Use only the clinic/vet details entered by the owner; do not invent a clinic address, phone number, response time or availability.
- `tel:` opens the device's call handler. `mailto:` creates an email draft.
- Copying or opening an email draft does not transmit it. The owner must review and send it.
- Emergency search is a generic map search; it is not a verified provider directory.

## Implementation boundary

The current backend can analyze uploaded face images and a baseline/current incision pair. It does not currently expose accounts, persistent records, medication reminders, message threads, doctor dashboards or alert delivery. The frontend should not simulate those capabilities. Those are future backend work, not UI-only actions.
