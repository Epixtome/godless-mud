# Google Cloud Deployment Guide - Godless V4.5

This document outlines the steps to deploy the Godless MUD engine to Google Cloud Platform (GCP).

## 1. Prerequisites
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed locally.
- A GCP Project with billing enabled.
- Artifact Registry or Container Registry API enabled.

## 2. Option A: Compute Engine (Recommended for MUDs)
Telnet MUDs require persistent TCP sockets. A VM on Compute Engine is the most straightforward host.

1. **Build and Tag the Image**:
   ```bash
   docker build -t gcr.io/[PROJECT_ID]/godless-mud:V4.5 .
   ```
2. **Push to Google Container Registry**:
   ```bash
   docker push gcr.io/[PROJECT_ID]/godless-mud:V4.5
   ```
3. **Create the Instance**:
   - Go to Compute Engine > VM Instances > Create.
   - select "Deploy a container image to this VM instance".
   - Image: `gcr.io/[PROJECT_ID]/godless-mud:V4.5`.
   - **Firewall**: Ensure Port `8888` is open in the VPC Firewall rules (Allow ingress TCP 8888 from 0.0.0.0/0).

## 3. Option B: Cloud Run (Serverless)
*Note: Cloud Run is best for HTTP, but supports "Direct VPC Egress" for TCP. Standard Telnet might experience timeouts if the process scales to zero.*

1. **Deploy**:
   ```bash
   gcloud run deploy godless-mud --source . --port 8888 --platform managed
   ```

## 4. Security & Persistence
- **Persistent Disk**: If using Compute Engine, ensure the `/app/data/saves` directory is mapped to a persistent volume so player data survives container restarts.
- **Firewall**: Only Port `8888` (Game) should be open. Keep SSH access restricted to your IP.

## 5. Local Prep (Git)
Ensure your `.gitignore` is active before pushing to a private GCP Repo:
1. `git rm -r --cached .` (To clear any files that were tracked but are now ignored)
2. `git add .`
3. `git commit -m "chore: prepare for GCP deployment with V4.5 architecture"`
