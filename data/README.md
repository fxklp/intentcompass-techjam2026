# Competition Data

## `public_set.jsonl`

Contains 200 labeled development sessions: 80 Buying, 80 Browsing, 30 Intent Override, and 10 Boundary sessions.

Each session contains a safe aggregate `user_profile` and public labels for local development. Direct user identifiers, timestamps, free-text reviews, raw purchase history, hidden intent cards, and simulator-policy internals are not shipped in this participant file.

## `catalog.jsonl`

From the repository root, run `python scripts/setup_data.py`. It downloads
`catalog.jsonl.gz` from the organizer's official `participant-kit` release,
checks SHA-256, and decompresses it as `catalog.jsonl` in this directory.
Expected row count: 50,000.

Never place API keys, private evaluation data, or participant outputs in this directory.
