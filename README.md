# PetTot — post-operative recovery tracking prototype

PetTot is a prototype for helping a pet owner record recovery observations, keep a local medication log, compare selected photos with experimental image-processing models, and prepare a concise update for their veterinary team. It is **not a diagnosis tool or an emergency service**.

## The intended owner journey

1. **Continue in demo mode.** The current build does not have real authentication, so it clearly labels this as a prototype rather than pretending to sign a user in.
2. **Set up a pet.** Enter the pet, procedure/date, clinic contacts and any instructions the veterinarian provided.
3. **Open the recovery overview.** See the recovery day, today's check-in status, medication ticks, recent notes and shortcuts to the next helpful task.
4. **Complete a brief check-in.** Record comfort, appetite, movement, visible incision changes, medication status and any urgent warning signs.
5. **Optionally review images.** Send a face photo to the grimace endpoint or a baseline/current incision photo pair to the incision endpoint.
6. **Decide what to do next.** Review the model's result with its limitations, contact the clinic using the details you supplied, or prepare and manually share a written summary.

The navigation is intentionally limited to **Overview**, **Daily check-in**, **Photo review**, and **Care & contacts**. Profile setup is a guided first step and can be reopened later.

## What works in this branch

- A unified responsive owner website with the step-by-step flow above.
- Pet profile saved in this browser's local storage.
- Dated owner check-ins and a simple medication-administration tick log saved in this browser.
- A connection test against `GET /health`.
- Real frontend requests to `POST /api/grimace/analyze` and `POST /api/incision/scan` when the backend is running.
- Result displays for the API's status, model score/metrics and optional generated preview/overlay.
- A vet-update text summary that the owner can copy or open as a draft in their email app. **Nothing is automatically sent to a clinic.**
- Legacy `code.html` entry points redirect to the new unified app.

## What is still a prototype / not implemented

- **No real login or account security.** The welcome screen starts a browser demo session only.
- **No database, account sync or server-side recovery history.** Profile, check-ins, medication ticks and the small analysis summary are stored locally in the browser. Clearing site data can remove them.
- **No push reminders or scheduled notifications.** A medication tick is a local record, not a timed alarm.
- **No veterinary inbox or dashboard, live chat, booking service or notification delivery.** The app does not notify a vet automatically.
- **No clinical validation implied by the image endpoints.** The current face pipeline totals four heuristic action units (maximum 8); this must not be described as a validated Feline Grimace Scale or Canine Grimace Scale without appropriate veterinary validation. The incision pipeline uses image-processing heuristics for a redness ratio and possible gaps; these cannot diagnose infection or confirm dehiscence.
- **No automated gait-video analysis**, structured veterinarian-authored treatment plan, or verified local emergency provider directory.

## Run locally

Use Python 3.10 or newer. From the repository root, create and activate a virtual environment, install the project's requirements, and start the API:

### Windows PowerShell — repository root

    py -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install -r requirements.txt
    uvicorn main:app --reload --host 127.0.0.1 --port 8000

### macOS / Linux — repository root

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -r requirements.txt
    uvicorn main:app --reload --host 127.0.0.1 --port 8000

Then open **http://127.0.0.1:8000/**. The frontend is served by FastAPI at the root, while `/health`, `/docs`, and the API endpoints remain available.

To serve the frontend separately during design work, run a second terminal with the working directory set to `frontend` and execute:

    python -m http.server 5500

Open http://127.0.0.1:5500/. In that setup, use the Photo review page to set the API base URL to `http://127.0.0.1:8000`. The backend CORS configuration permits the local development origin. Avoid exposing this development server to a public network.

### Gemini fallback

The face pipeline may use a Gemini fallback depending on model output. Configure `GEMINI_API_KEY` only in the backend environment if that integration is needed. Do not place the key in frontend JavaScript or commit it to the repository. The app should be evaluated without assuming a fallback will always be available.

## API endpoints

- `GET /health` — liveness and model names.
- `POST /api/grimace/analyze` — multipart fields: `file` (image), `baseline_mar` (float, default 2.0), `force_fallback` (boolean, default false).
- `POST /api/incision/scan` — multipart fields: `day1_file` (baseline image), `dayN_file` (current image), optional `crop_x`, `crop_y`, `crop_w`, `crop_h` values.
- `GET /docs` — interactive FastAPI/OpenAPI documentation.

The browser rejects image files over 15 MB; server-side upload limits and production validation still need to be implemented. Images are sent to the configured API URL when an analysis is requested. Do not send images to a backend you do not trust.

## Safety and clinical language

The app records **owner observations**. It does not interpret check-in responses as a diagnosis. Obvious emergency warning signs are kept separate from the image tools so owners are not encouraged to wait for a model result. If breathing is difficult, a pet collapses, bleeding is uncontrolled, or a severe/sudden change occurs, seek urgent veterinary care. These broad reminders are informed by [AAHA public emergency guidance](https://www.aaha.org/resources/help-is-this-a-pet-emergency/) and [VCA post-operative guidance](https://vcahospitals.com/veterinary-care/primary/know-your-pet/post-operative-instructions-in-dogs); they are not exhaustive and do not override your clinic's instructions.

A model's `GREEN` status means only that the current heuristic did not flag a change. It does not rule out pain, infection, or a surgical complication. A `RED` result does not mean a vet has been notified. The interface says this explicitly.

Before using this with real clients, veterinary professionals should review the scales, thresholds, guidance, species-specific language, accessibility, privacy and all emergency wording. Add tested authentication, authorization, durable storage, auditability, rate limiting, file validation, retention/deletion controls and a real care-team workflow before any public deployment.

## Suggested next engineering steps

1. Have a veterinarian review and approve the check-in questions, escalation rules, medication wording and clinical disclaimers.
2. Define a durable API schema for pet profiles, check-ins, photos, medication schedules and clinician responses.
3. Add real authentication, owner/veterinarian roles, per-pet access control and a database.
4. Add consent, retention/deletion controls, safe image handling, server-side size/type validation, rate limits and production CORS rules.
5. Build an actual care-team dashboard and delivery/acknowledgement workflow before claiming that a vet has received an alert.
6. Validate the image models prospectively against veterinarian-reviewed data before showing clinical performance or validated-scale claims.

## Visual direction and photo credits

The owner interface uses an editorial veterinary-care design: wide photo-backed hero banners, dark-to-warm gradient overlays, high-contrast serif headlines, restrained action panels and consistent spacing. The welcome, overview, check-in, photo-review and care-contact pages share the same visual language. Images are currently served from Unsplash so this prototype needs an internet connection to show them. The site hides a failed image and falls back to a designed color panel if the image host is unreachable. Before public deployment, review the Unsplash License and consider self-hosting appropriately licensed, optimized copies.

Image sources used in this prototype (each source page identifies the photo as free to use under the Unsplash License):

- Dog and cat together — [Anusha Barwa on Unsplash](https://unsplash.com/photos/shallow-focus-photography-of-dog-and-cat-ppKcYi1CXcI).
- Dog resting on a bed — [Joshua Chun on Unsplash](https://unsplash.com/photos/dog-sleeping-on-bed-Nhgva0MVRmc).
- Veterinarian examining a dog — [Alexander Mass on Unsplash](https://unsplash.com/photos/veterinarian-examines-a-dog-on-an-examination-table-I3KxEBS6iOc).
- Cat wrapped in a cozy blanket — [Marco J Haenssgen on Unsplash](https://unsplash.com/photos/a-cute-cat-wrapped-in-a-cozy-blanket-KCQpk2QR25k).

The visual direction is informed by veterinary website design guidance emphasizing reassurance, clear next actions and easy-to-find contact paths, as well as W3C contrast guidance for text over images. References: [veterinary website design patterns](https://onyxarro.com/blog/veterinary-website-design-examples) and [W3C WCAG contrast minimum](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum). This is an original interface treatment, not a reproduction of another site.

## Repository overview

- `main.py` — FastAPI app, two image-analysis endpoints and static frontend serving.
- `models/Visual_Grimace_Calculator/` — face landmark/metric pipeline and optional Gemini fallback.
- `models/Incision_Change_Detection/` — image preprocessing, redness segmentation and gap heuristic.
- `frontend/index.html` — unified owner flow.
- `frontend/styles.css` — responsive, restrained visual system.
- `frontend/app.js` — route state, browser-local demo records and real API requests.
- `frontend/USER_FLOW.md` — screen-by-screen flow and build decisions.
