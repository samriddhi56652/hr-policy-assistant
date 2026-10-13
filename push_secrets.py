"""push_secrets.py — copy the API keys from .env into Google Secret Manager.

    python push_secrets.py

No key is ever printed or typed by hand. Run it again after changing a key:
it adds a new version of the secret, and Cloud Run uses the latest one.
"""

import subprocess

from dotenv import dotenv_values

PROJECT = "hr-rag-assistant-510309"
SERVICE_ACCOUNT = "hr-assistant-run@hr-rag-assistant-510309.iam.gserviceaccount.com"

# name in .env  ->  name in Secret Manager
SECRETS = {
    "JINA_API_KEY": "jina-api-key",
    "QDRANT_API_KEY": "qdrant-api-key",
    "GROQ_API_KEY": "groq-api-key",
}


def gcloud(*args: str, data: str | None = None) -> subprocess.CompletedProcess:
    # shell=True because on Windows gcloud is a .cmd script
    return subprocess.run(["gcloud", *args, f"--project={PROJECT}"],
                          input=data, capture_output=True, text=True, shell=True)


def main() -> None:
    env = dotenv_values(".env")
    for env_name, secret_name in SECRETS.items():
        value = (env.get(env_name) or "").strip()
        if not value or "paste-" in value:
            print(f"SKIPPED {secret_name}: {env_name} is empty in .env")
            continue

        # Create the secret the first time; add a new version after that.
        exists = gcloud("secrets", "describe", secret_name).returncode == 0
        if exists:
            result = gcloud("secrets", "versions", "add", secret_name, "--data-file=-", data=value)
        else:
            result = gcloud("secrets", "create", secret_name, "--replication-policy=automatic",
                            "--data-file=-", data=value)
        if result.returncode != 0:
            print(f"FAILED {secret_name}: {result.stderr.strip()[:300]}")
            continue

        # Only the app's own account may read it — this one secret, not the whole project.
        grant = gcloud("secrets", "add-iam-policy-binding", secret_name,
                       f"--member=serviceAccount:{SERVICE_ACCOUNT}",
                       "--role=roles/secretmanager.secretAccessor", "--condition=None")
        if grant.returncode != 0:
            print(f"FAILED to grant access to {secret_name}: {grant.stderr.strip()[:300]}")
            continue

        # Read it back and compare with .env — without printing it.
        stored = gcloud("secrets", "versions", "access", "latest", f"--secret={secret_name}").stdout.strip()
        check = "matches .env - OK" if stored == value else "DOES NOT MATCH .env - check it"
        print(f"{'UPDATED' if exists else 'CREATED'} {secret_name}: {check}")


if __name__ == "__main__":
    main()
    