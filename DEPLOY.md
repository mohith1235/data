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
2. In **Authentication → Providers → Email**, enable email/password sign-up.
   Disable **Confirm Email**. Supabase requires an email-shaped internal identity
   for password authentication; the app maps each user ID to a private
   non-deliverable address at `users.dataintelligence.invalid`. Users do not enter
   or receive email.
3. If you configure authentication redirect URLs, set the site URL to
   `https://dataintelligence.streamlit.app`.
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
6. Users choose a 3-32 character ID using letters, numbers, underscores, or
   hyphens and a password with at least 8 characters. IDs are case-insensitive.
7. There is no email-based password reset. If someone forgets a password, the
   project administrator must reset their account through a trusted Supabase
   admin workflow. Never put the Supabase service-role key in this app.
8. Accounts created previously with real email addresses are not automatically
   converted to user IDs.

Account credentials are handled by Supabase Auth. Uploaded CSV files and
analysis results remain session-only; this app does not persist user datasets.
