import sys
from unittest.mock import MagicMock

# Bloqueia imports de SDKs GCP antes que os agentes sejam carregados.
# Permite rodar pytest sem instalar google-cloud-aiplatform ou google-cloud-firestore.
sys.modules["vertexai"] = MagicMock()
sys.modules["vertexai.generative_models"] = MagicMock()
sys.modules["google.cloud"] = MagicMock()
sys.modules["google.cloud.firestore"] = MagicMock()
