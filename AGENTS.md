# Production safety rules

- Preserve the user’s original script and supplied art. Never substitute blanks or pretend a reconstruction is the original audio.
- After creating or changing a meaningful source, plan, prompt, timing, audio or asset file, commit and push a checkpoint before the next major operation. A local commit alone is not a backup.
- Run `python source/checkpoint.py "Describe the completed stage"`. Authentication must come from the environment or a private credential helper outside the repository.
- The checkpoint must scan for credentials, push successfully and verify that remote `main` equals local HEAD. Stop rather than silently proceeding after a backup failure.
- Checkpoint every completed narration chunk. Save lossless processed audio as FLAC; WAV files are reproducible intermediates and are not backed up. Run `bash source/restore_audio.sh` to reconstruct narration WAV.
- Never commit .env files, credentials, private workspace exports or raw session logs.
- Preserve the existing private repository visibility. Do not trigger full video rendering or publication from a push.
- The user explicitly authorized the full MP4 build. Render only from a verified checkpoint; keep one active render per target. No Shorts or thumbnail are requested.
- Recovered source is not final validated source. Check dependencies, timing, captions, typography, alpha mattes and actual motion before marking QA passed. Historical review notes are not a new inspection.
- Check `audio/status.json` and existing jobs before retrying synthesis. Do not duplicate an in-flight request.
