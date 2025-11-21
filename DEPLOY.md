# Deployment Instructions

This application is ready to be deployed to **Vercel**.

## Prerequisites

1.  **GitHub Account**: You need to push this code to a GitHub repository.
2.  **Vercel Account**: Sign up at [vercel.com](https://vercel.com).

## Steps

1.  **Push to GitHub**:
    *   Initialize a git repo: `git init`
    *   Add files: `git add .`
    *   Commit: `git commit -m "Initial commit"`
    *   Push to your GitHub repository.

2.  **Deploy on Vercel**:
    *   Go to your Vercel Dashboard.
    *   Click **"Add New..."** -> **"Project"**.
    *   Import your GitHub repository.
    *   **Environment Variables**:
        *   You need a Postgres database. You can add **Vercel Postgres** from the Storage tab in your Vercel project.
        *   Once added, Vercel automatically sets the `POSTGRES_URL` (or `DATABASE_URL`) environment variable.
    *   Click **Deploy**.

3.  **Database Initialization**:
    *   The app attempts to initialize the database on start, but for the very first run, you might need to verify the tables are created. The `init_db()` function in `app.py` handles this.

4.  **Cron Jobs**:
    *   The `vercel.json` file includes a cron job configuration to hit `/run-today` every day at 6 AM UTC. This replaces the local scheduler.

## Important Notes

*   **Statelessness**: Invoices are generated on-the-fly when you click "Download". They are not stored on the server.
*   **Base Template**: Ensure `base_invoice_template.docx` is included in your repository (it is by default).
