# Weekly Shabbat block

The homepage includes `_includes/next-shabbat.html`. During the Pages build,
`update_parasha.py` fetches Hebcal data for the coming Saturday and generates
`_data/next_shabbat.json`. Generated data is ignored by Git; no weekly commits
are needed. Double portions link to both existing parasha pages. Festival
Shabbatot display the festival reading instead.

## Enable deployment

1. Push the reviewed changes to the default branch, `main`.
2. In GitHub, select **Settings → Pages → Build and deployment → Source → GitHub Actions**.
3. Run **Build and deploy Pages** from the Actions tab for the first deployment.

The workflow runs on pushes to `main`, manually, and each Sunday at 01:00
Europe/Amsterdam (including daylight-saving changes). GitHub can delay scheduled
runs and disables public-repository schedules after 60 days without activity.
Re-enable the workflow in Actions if necessary.

The default is the Diaspora reading cycle. Set `HEBCAL_ISRAEL` to `"on"` in
the workflow for the Israel cycle. No Hebcal API key or personal token is needed.
An API or mapping failure stops the build before deployment.

## Local checks and previews

```powershell
python -m unittest discover -s scripts -p "test_*.py"
python scripts/update_parasha.py --date 2026-11-08
```

The date override previews the coming Shabbat relative to the supplied date.
On Windows, running without `--date` requires the Python `tzdata` package;
the Ubuntu Actions runner already has timezone data. To preview the HTML,
generate the JSON first, then build the site with Jekyll.

References:
- https://www.hebcal.com/home/195/jewish-calendar-rest-api
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule
- https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages
