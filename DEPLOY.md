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
