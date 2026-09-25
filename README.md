# Funny-Memes

This repository automatically collects 50 funny meme posts every day from public Reddit meme communities and saves the results in the repository.

## Outputs

- `data/daily_memes.json` stores the daily feed as structured data.
- `data/daily_memes.md` stores the same feed in a readable Markdown format.

## Automation

The workflow at `.github/workflows/daily-memes.yml` is scheduled to run daily around 12:00 UTC and can also be triggered manually.

## Local usage

Run the collector locally with:

```bash
python scripts/fetch_memes.py
```

Optional flags:

- `--count` to change how many memes are collected.
- `--subreddit` to override the default subreddit list.
- `--output-json` and `--output-markdown` to change output paths.
