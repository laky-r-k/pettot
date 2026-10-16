# Apply this redesign to `Anvith-Branch`

This archive is an overlay for the existing repository: it contains only changed/new files, so the existing `models/` and `requirements.txt` stay in place.

## Windows PowerShell

1. Download and extract `pettot-professional-overlay.zip`.
2. Open PowerShell in your existing local clone of the `Anvith-Branch` repository.
3. Review the current branch and working tree:

       git switch Anvith-Branch
       git status

4. Copy/extract the archive contents into the repository root, allowing the included `README.md`, `main.py`, and `frontend/` files to replace their old versions.
5. The editorial visual pass uses Unsplash-hosted images and Google Fonts, so photos and the selected font pair need an internet connection. Attribution/links are documented in `README.md`. Failed photo loads fall back to designed color blocks; fonts fall back to installed serif/sans-serif fonts.
6. Inspect exactly what changed before committing:

       git status
       git diff --stat
       git diff -- README.md main.py frontend

7. Run the syntax checks and start the backend, as described in the README. Then commit and push after you are satisfied with the diff:

       git add README.md main.py frontend
       git commit -m "Refine PetTot editorial recovery UI"
       git push origin Anvith-Branch

Do not commit API keys or real pet/client data.
