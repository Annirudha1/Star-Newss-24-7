# STAR NEWS 24×7

Django site for the STAR NEWS 24×7 publication. Publisher identity: Sunil Sharma. Website and Android app development/technical support are credited separately to Anirudha Pandey.

## Original news content

STAR NEWS 24×7 produces original news reporting and video coverage. News items are managed in Django admin as `NewsVideo` records. Add a byline, publication/update details, and media credits only when confirmed; do not guess missing information. RSS importing and feed/article admin screens are not used.

The RSS/article database tables from the prior schema change are intentionally retained to avoid deleting any existing records. They are not shown on public pages or registered in Django admin. Remove any existing server cron/scheduler entries that run `manage.py fetch_news`; the importer has been removed.

## Deployment

From the deployed project root, with the production environment variables and virtual environment already configured:

```sh
python manage.py check --deploy
python manage.py migrate --noinput
python manage.py collectstatic --noinput
```

The existing `Procfile` defines the web process:

```sh
gunicorn --bind 127.0.0.1:8000 --workers=1 --threads=15 starnews_project.wsgi:application
```

Use the existing server process manager to restart that process after deployment. The repository does not specify the server's absolute project path, Python executable, or process-manager name.

## Public policy pages

- About: `/about/`
- Contact: `/contact/`
- Editorial Policy: `/editorial-policy/`
- Corrections Policy: `/corrections-policy/`
- Privacy Policy: `/privacy-policy/`
- Terms & Conditions: `/terms-and-conditions/`
- News Sources / Attribution: `/news-sources/`
