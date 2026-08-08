# PMD (Pakistan Meteorological Department)

- UPDATE: uses a real CAP alerts feed, no scraping needed:
  https://cap-sources.s3.amazonaws.com/pk-pmd-en/rss.xml
- pmd.gov.pk itself now says the site is archived/no longer updated (the
  live site is weather.gov.pk) but this alert feed is hosted separately on
  AWS and remains active.
- No key required. Parsed via feedparser (already in requirements.txt).
- Content is free-text regional advisories (floods, heavy rain, drought) -
  not numeric readings, so stored as metric_type='alert'.
- Quirks: none else discovered yet - update this file as you find them.
