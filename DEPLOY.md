# Deployment guide

This project is ready to deploy as a Streamlit app.

## Local run

```bash
python -m streamlit run app.py
```

## Streamlit Community Cloud

1. Push this folder to a GitHub repository.
2. Open https://share.streamlit.io/
3. Sign in with GitHub.
4. Select the repository.
5. Set the app file to `app.py`.
6. Click Deploy.

Expected public URL format:

```text
https://<repository-name>.streamlit.app
```

If the repository name is `data-intelligence-system`, the public URL will be:

```text
https://data-intelligence-system.streamlit.app
```

## Uploading data

The sample dataset is intentionally excluded from the public repository. After
deployment, upload a CSV from the dashboard sidebar to use the overview, quality,
exploration, and modeling features.

## Supabase accounts

1. Create a Supabase project on the free tier.
2. In **Authentication → Providers → Email**, enable email/password sign-up and
   configure email confirmation as desired.
3. In **Authentication → URL Configuration**, set the site URL to
   `https://dataintelligence.streamlit.app` and allow that URL for redirects.
4. In the Supabase project's **API Keys** settings, copy the project URL and its
   publishable key (or legacy anon key). Do not use the `service_role` or secret
   key in this app.
5. In Streamlit Community Cloud, open the app's **Settings → Secrets** and add:

   ```toml
   [supabase]
   url = "https://YOUR_PROJECT.supabase.co"
   anon_key = "YOUR_SUPABASE_PUBLISHABLE_OR_ANON_KEY"
   ```

   A placeholder template is available at
   `.streamlit/secrets.toml.example`. Never commit the populated
   `.streamlit/secrets.toml` file or share credentials in chat.
6. To enable password recovery codes, edit the Supabase **Authentication → Email
   Templates → Reset Password** template and include `{{ .Token }}` in the
   message. Users request a code in the app, then enter it with a new password.
7. If email confirmation is enabled, users must confirm their address from the
   email before signing in.

Account credentials are handled by Supabase Auth. Uploaded CSV files and
analysis results remain session-only; this app does not persist user datasets.
