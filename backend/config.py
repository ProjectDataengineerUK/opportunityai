import os
import yaml
from functools import lru_cache
from pydantic import BaseModel


class GeminiConfig(BaseModel):
    default_model: str = "gemini-2.5-flash"
    advanced_model: str = "gemini-2.5-pro"


class SourcesConfig(BaseModel):
    remoteok: bool = True
    remotive: bool = True
    freelancer: bool = True
    upwork: bool = False
    workana: bool = True


class AppConfig(BaseModel):
    user_profile: dict
    score_weights: dict
    decision_thresholds: dict
    gemini: GeminiConfig
    sources: SourcesConfig
    freelancer_client_id: str = ""
    freelancer_token: str = ""
    upwork_token: str = ""
    upwork_org_id: str = ""
    gcp_project_id: str = ""
    gcp_location: str = "us-central1"


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    config_path = os.getenv("CONFIG_PATH", "/app/config.yaml")
    if not os.path.exists(config_path):
        config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")

    with open(config_path) as f:
        data = yaml.safe_load(f)

    data["freelancer_client_id"] = os.getenv("FREELANCER_CLIENT_ID", "")
    data["freelancer_token"] = os.getenv("FREELANCER_TOKEN", "")
    data["upwork_token"] = os.getenv("UPWORK_TOKEN", "")
    data["upwork_org_id"] = os.getenv("UPWORK_ORG_ID", "")
    data["gcp_project_id"] = os.getenv("GCP_PROJECT_ID", "")
    data["gcp_location"] = os.getenv("GCP_LOCATION", "us-central1")

    return AppConfig(**data)
