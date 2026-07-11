"""
Unit Tests - ML Inference API
Tests machine learning model inference using mocked dependencies.

Author: Ayoub Hamrouni
Mission: OPERATION ARGUS-TEST
Date: 2025-10-22
"""

import pickle
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "ml_training"))


# ============================================================================
# Model Loading Tests
# ============================================================================

@pytest.mark.unit
class TestModelLoading:
    """Test ML model loading and initialization"""

    @patch("inference_api.pickle.load")
    @patch("builtins.open", new_callable=mock_open)
    def test_load_random_forest_model(self, mock_file, mock_pickle):
        mock_model = MagicMock()
        mock_pickle.return_value = mock_model

        with patch("inference_api.MODEL_PATH", Path("/tmp/models")):
            from inference_api import load_models
            with patch.object(Path, "exists", return_value=True):
                import inference_api as api
                api.models.clear()
                api.scaler = None
                api.label_encoder = None
                api.feature_names = None
                load_models()

                assert "random_forest" in api.models
                assert api.models["random_forest"] is mock_model

    @patch("inference_api.pickle.load")
    @patch("builtins.open", new_callable=mock_open)
    def test_load_scaler(self, mock_file, mock_pickle):
        mock_scaler = MagicMock()
        mock_scaler.transform = MagicMock(return_value=np.array([[0.0] * 77]))
        mock_pickle.return_value = mock_scaler

        import inference_api as api
        api.models.clear()
        api.scaler = None
        api.label_encoder = None
        api.feature_names = None

        with patch.object(Path, "exists", return_value=True):
            api.load_models()

        assert api.scaler is mock_scaler
        X = np.array([[1.0] * 77])
        X_scaled = api.scaler.transform(X)
        assert X_scaled.shape == (1, 77)

    @patch("inference_api.pickle.load")
    @patch("builtins.open", new_callable=mock_open)
    def test_load_label_encoder(self, mock_file, mock_pickle):
        mock_encoder = MagicMock()
        mock_encoder.classes_ = np.array(["BENIGN", "ATTACK"])
        mock_encoder.inverse_transform.return_value = np.array(["ATTACK"])

        dummy = MagicMock()
        mock_pickle.side_effect = [dummy, dummy, dummy, dummy, mock_encoder, dummy]

        import inference_api as api
        api.models.clear()
        api.scaler = None
        api.label_encoder = None
        api.feature_names = None

        with patch.object(Path, "exists", return_value=True):
            api.load_models()

        assert api.label_encoder is mock_encoder
        result = api.label_encoder.inverse_transform([1])
        assert result[0] == "ATTACK"

    @patch("inference_api.pickle.load")
    @patch("builtins.open", new_callable=mock_open)
    def test_missing_model_files_raises_runtime_error(self, mock_file, mock_pickle):
        mock_pickle.return_value = MagicMock()

        import inference_api as api
        api.models.clear()
        api.scaler = None
        api.label_encoder = None
        api.feature_names = None

        with patch.object(Path, "exists", return_value=False):
            with pytest.raises(RuntimeError, match="No models loaded"):
                api.load_models()

    @patch("inference_api.pickle.load")
    @patch("builtins.open", new_callable=mock_open)
    def test_corrupt_model_file_handled(self, mock_file, mock_pickle):
        mock_pickle.side_effect = pickle.UnpicklingError("corrupt data")

        import inference_api as api
        api.models.clear()
        api.scaler = None
        api.label_encoder = None
        api.feature_names = None

        with patch.object(Path, "exists", return_value=True):
            with pytest.raises(RuntimeError, match="No models loaded"):
                api.load_models()


# ============================================================================
# Feature Validation Tests
# ============================================================================

@pytest.mark.unit
class TestFeatureValidation:
    """Test network flow feature validation"""

    def test_valid_feature_count(self, sample_network_flow):
        from inference_api import NetworkFlow
        flow = NetworkFlow(**sample_network_flow)
        assert len(flow.features) == 77

    def test_invalid_feature_count_too_few(self):
        from inference_api import NetworkFlow
        with pytest.raises(Exception):
            NetworkFlow(features=[0.0] * 50, model_name="random_forest")

    def test_invalid_feature_count_too_many(self):
        from inference_api import NetworkFlow
        with pytest.raises(Exception):
            NetworkFlow(features=[0.0] * 100, model_name="random_forest")

    def test_empty_features_rejected(self):
        from inference_api import NetworkFlow
        with pytest.raises(Exception):
            NetworkFlow(features=[], model_name="random_forest")

    def test_feature_types_are_numeric(self, sample_network_flow):
        from inference_api import NetworkFlow
        flow = NetworkFlow(**sample_network_flow)
        for feature in flow.features:
            assert isinstance(feature, float)

    def test_nan_values_accepted_by_pydantic(self):
        from inference_api import NetworkFlow
        flow = NetworkFlow(features=[float("nan")] * 77, model_name="random_forest")
        assert any(np.isnan(f) for f in flow.features)

    def test_string_features_rejected(self):
        from inference_api import NetworkFlow
        with pytest.raises(Exception):
            NetworkFlow(features=["not_a_number"] * 77, model_name="random_forest")


# ============================================================================
# Prediction Tests
# ============================================================================

@pytest.mark.unit
class TestPredictions:
    """Test ML model predictions"""

    def _setup_api(self):
        import inference_api as api
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([1])
        mock_model.predict_proba.return_value = np.array([[0.05, 0.95]])

        mock_encoder = MagicMock()
        mock_encoder.classes_ = np.array(["BENIGN", "ATTACK"])
        mock_encoder.inverse_transform.return_value = np.array(["ATTACK"])

        mock_scaler = MagicMock()
        mock_scaler.transform.return_value = np.random.randn(1, 77)

        api.models = {"random_forest": mock_model}
        api.scaler = mock_scaler
        api.label_encoder = mock_encoder
        api.feature_names = [f"feat_{i}" for i in range(77)]
        return api

    @pytest.mark.asyncio
    async def test_prediction_returns_correct_format(self):
        from inference_api import NetworkFlow
        api = self._setup_api()

        flow = NetworkFlow(features=[0.0] * 77, model_name="random_forest")
        response = await api.predict(flow)

        assert response.prediction in ("BENIGN", "ATTACK")
        assert 0.0 <= response.confidence <= 1.0
        assert "BENIGN" in response.probabilities
        assert "ATTACK" in response.probabilities
        assert response.model_used == "random_forest"
        assert response.inference_time_ms >= 0
        assert response.timestamp is not None

    @pytest.mark.asyncio
    async def test_confidence_is_max_probability(self):
        from inference_api import NetworkFlow
        api = self._setup_api()

        flow = NetworkFlow(features=[0.0] * 77, model_name="random_forest")
        response = await api.predict(flow)

        assert response.confidence == pytest.approx(0.95, abs=0.01)

    @pytest.mark.asyncio
    async def test_probabilities_sum_to_one(self):
        from inference_api import NetworkFlow
        api = self._setup_api()

        flow = NetworkFlow(features=[0.0] * 77, model_name="random_forest")
        response = await api.predict(flow)

        total = sum(response.probabilities.values())
        assert total == pytest.approx(1.0, abs=0.001)

    @pytest.mark.asyncio
    async def test_benign_prediction(self):
        from inference_api import NetworkFlow
        api = self._setup_api()
        api.models["random_forest"].predict.return_value = np.array([0])
        api.models["random_forest"].predict_proba.return_value = np.array([[0.98, 0.02]])
        api.label_encoder.inverse_transform.return_value = np.array(["BENIGN"])

        flow = NetworkFlow(features=[0.0] * 77, model_name="random_forest")
        response = await api.predict(flow)

        assert response.prediction == "BENIGN"
        assert response.confidence == pytest.approx(0.98, abs=0.01)

    @pytest.mark.asyncio
    async def test_prediction_without_scaler(self):
        from inference_api import NetworkFlow
        api = self._setup_api()
        api.scaler = None

        flow = NetworkFlow(features=[0.0] * 77, model_name="random_forest")
        response = await api.predict(flow)

        assert response.prediction in ("BENIGN", "ATTACK")

    @pytest.mark.asyncio
    async def test_invalid_model_name_rejected(self):
        from inference_api import NetworkFlow
        api = self._setup_api()

        flow = NetworkFlow(features=[0.0] * 77, model_name="nonexistent_model")
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await api.predict(flow)
        assert exc_info.value.status_code == 400


# ============================================================================
# Model Selection Tests
# ============================================================================

@pytest.mark.unit
class TestModelSelection:
    """Test model selection and routing"""

    def _setup_api(self, model_names):
        import inference_api as api
        api.models = {}
        for name in model_names:
            mock_model = MagicMock()
            mock_model.predict.return_value = np.array([0])
            mock_model.predict_proba.return_value = np.array([[0.9, 0.1]])
            api.models[name] = mock_model
        api.scaler = MagicMock()
        api.scaler.transform.return_value = np.random.randn(1, 77)
        api.label_encoder = MagicMock()
        api.label_encoder.classes_ = np.array(["BENIGN", "ATTACK"])
        api.label_encoder.inverse_transform.return_value = np.array(["BENIGN"])
        api.feature_names = [f"feat_{i}" for i in range(77)]
        return api

    def test_random_forest_is_valid_model(self):
        api = self._setup_api(["random_forest", "xgboost", "decision_tree"])
        assert "random_forest" in api.models

    def test_xgboost_is_valid_model(self):
        api = self._setup_api(["random_forest", "xgboost", "decision_tree"])
        assert "xgboost" in api.models

    def test_decision_tree_is_valid_model(self):
        api = self._setup_api(["random_forest", "xgboost", "decision_tree"])
        assert "decision_tree" in api.models

    def test_invalid_model_name_not_in_models(self):
        api = self._setup_api(["random_forest", "xgboost", "decision_tree"])
        assert "svm" not in api.models
        assert "neural_network" not in api.models
        assert "invalid_model" not in api.models


# ============================================================================
# API Endpoint Tests (mocked HTTP)
# ============================================================================

@pytest.mark.unit
@pytest.mark.asyncio
class TestMLInferenceEndpoints:
    """Test ML Inference API endpoints using FastAPI TestClient"""

    def _setup_api(self):
        import inference_api as api
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([1])
        mock_model.predict_proba.return_value = np.array([[0.05, 0.95]])
        api.models = {"random_forest": mock_model}
        api.scaler = MagicMock()
        api.scaler.transform.return_value = np.random.randn(1, 77)
        api.label_encoder = MagicMock()
        api.label_encoder.classes_ = np.array(["BENIGN", "ATTACK"])
        api.label_encoder.inverse_transform.return_value = np.array(["ATTACK"])
        api.feature_names = [f"feat_{i}" for i in range(77)]
        return api

    def test_health_endpoint(self):
        from fastapi.testclient import TestClient
        api = self._setup_api()
        client = TestClient(api.app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "models_loaded" in data
        assert data["status"] == "healthy"

    def test_models_endpoint(self):
        from fastapi.testclient import TestClient
        api = self._setup_api()
        client = TestClient(api.app)
        response = client.get("/models")
        assert response.status_code == 200
        data = response.json()
        assert "total_models" in data
        assert "models" in data
        assert data["total_models"] == 1
        assert "random_forest" in data["models"]

    def test_predict_endpoint(self, sample_network_flow):
        from fastapi.testclient import TestClient
        api = self._setup_api()
        client = TestClient(api.app)
        response = client.post("/predict", json=sample_network_flow)
        assert response.status_code == 200
        data = response.json()
        assert "prediction" in data
        assert "confidence" in data
        assert "model_used" in data
        assert data["prediction"] in ["BENIGN", "ATTACK"]
        assert 0.0 <= data["confidence"] <= 1.0

    def test_predict_invalid_model_returns_400(self):
        from fastapi.testclient import TestClient
        api = self._setup_api()
        client = TestClient(api.app)
        response = client.post("/predict", json={
            "features": [0.0] * 77,
            "model_name": "nonexistent"
        })
        assert response.status_code == 400

    def test_predict_wrong_feature_count_returns_422(self):
        from fastapi.testclient import TestClient
        api = self._setup_api()
        client = TestClient(api.app)
        response = client.post("/predict", json={
            "features": [0.0] * 50,
            "model_name": "random_forest"
        })
        assert response.status_code == 422

    def test_root_endpoint(self):
        from fastapi.testclient import TestClient
        api = self._setup_api()
        client = TestClient(api.app)
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "CICIDS2017 Intrusion Detection API"
        assert "random_forest" in data["models_loaded"]


# ============================================================================
# Edge Case Tests
# ============================================================================

@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def _setup_api(self):
        import inference_api as api
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([0])
        mock_model.predict_proba.return_value = np.array([[0.6, 0.4]])
        api.models = {"random_forest": mock_model}
        api.scaler = MagicMock()
        api.scaler.transform.return_value = np.random.randn(1, 77)
        api.label_encoder = MagicMock()
        api.label_encoder.classes_ = np.array(["BENIGN", "ATTACK"])
        api.label_encoder.inverse_transform.return_value = np.array(["BENIGN"])
        api.feature_names = [f"feat_{i}" for i in range(77)]
        return api

    @pytest.mark.asyncio
    async def test_all_zeros_input(self):
        from inference_api import NetworkFlow
        api = self._setup_api()
        flow = NetworkFlow(features=[0.0] * 77, model_name="random_forest")
        response = await api.predict(flow)
        assert response.prediction in ("BENIGN", "ATTACK")

    @pytest.mark.asyncio
    async def test_extreme_positive_values(self):
        from inference_api import NetworkFlow
        api = self._setup_api()
        flow = NetworkFlow(features=[1e10] * 77, model_name="random_forest")
        response = await api.predict(flow)
        assert response.prediction in ("BENIGN", "ATTACK")
        assert 0.0 <= response.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_extreme_negative_values(self):
        from inference_api import NetworkFlow
        api = self._setup_api()
        flow = NetworkFlow(features=[-1e10] * 77, model_name="random_forest")
        response = await api.predict(flow)
        assert response.prediction in ("BENIGN", "ATTACK")

    @pytest.mark.asyncio
    async def test_mixed_extreme_values(self):
        from inference_api import NetworkFlow
        api = self._setup_api()
        features = [0.0] * 77
        features[0] = 1e15
        features[38] = -1e15
        features[76] = float("inf")
        flow = NetworkFlow(features=features, model_name="random_forest")
        response = await api.predict(flow)
        assert response.prediction in ("BENIGN", "ATTACK")

    @pytest.mark.asyncio
    async def test_batch_prediction_limit(self):
        from fastapi.testclient import TestClient
        api = self._setup_api()
        client = TestClient(api.app)
        flows = {"features": [0.0] * 77, "model_name": "random_forest"}
        response = client.post("/predict/batch", json=[flows] * 1001)
        assert response.status_code == 400


# ============================================================================
# Security Validation Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.security
class TestSecurityValidation:
    """Test security aspects of ML inference"""

    def test_sql_injection_in_model_name(self):
        from fastapi.testclient import TestClient
        import inference_api as api
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([0])
        mock_model.predict_proba.return_value = np.array([[0.9, 0.1]])
        api.models = {"random_forest": mock_model}
        api.scaler = MagicMock()
        api.scaler.transform.return_value = np.random.randn(1, 77)
        api.label_encoder = MagicMock()
        api.label_encoder.classes_ = np.array(["BENIGN", "ATTACK"])
        api.label_encoder.inverse_transform.return_value = np.array(["BENIGN"])
        api.feature_names = [f"feat_{i}" for i in range(77)]

        client = TestClient(api.app)
        response = client.post("/predict", json={
            "features": [0.0] * 77,
            "model_name": "'; DROP TABLE models; --"
        })
        assert response.status_code == 400

    def test_path_traversal_in_model_name(self):
        from fastapi.testclient import TestClient
        import inference_api as api
        mock_model = MagicMock()
        api.models = {"random_forest": mock_model}
        api.scaler = MagicMock()
        api.label_encoder = MagicMock()
        api.label_encoder.classes_ = np.array(["BENIGN", "ATTACK"])
        api.feature_names = [f"feat_{i}" for i in range(77)]

        client = TestClient(api.app)
        response = client.post("/predict", json={
            "features": [0.0] * 77,
            "model_name": "../../../etc/passwd"
        })
        assert response.status_code == 400

    def test_extremely_long_model_name(self):
        from fastapi.testclient import TestClient
        import inference_api as api
        api.models = {"random_forest": MagicMock()}
        api.scaler = MagicMock()
        api.label_encoder = MagicMock()
        api.label_encoder.classes_ = np.array(["BENIGN", "ATTACK"])
        api.feature_names = [f"feat_{i}" for i in range(77)]

        client = TestClient(api.app)
        response = client.post("/predict", json={
            "features": [0.0] * 77,
            "model_name": "A" * 10000
        })
        assert response.status_code == 400

    def test_xss_in_model_name(self):
        from fastapi.testclient import TestClient
        import inference_api as api
        api.models = {"random_forest": MagicMock()}
        api.scaler = MagicMock()
        api.label_encoder = MagicMock()
        api.label_encoder.classes_ = np.array(["BENIGN", "ATTACK"])
        api.feature_names = [f"feat_{i}" for i in range(77)]

        client = TestClient(api.app)
        response = client.post("/predict", json={
            "features": [0.0] * 77,
            "model_name": "<script>alert('xss')</script>"
        })
        assert response.status_code == 400

    def test_empty_model_name(self):
        from fastapi.testclient import TestClient
        import inference_api as api
        api.models = {"random_forest": MagicMock()}
        api.scaler = MagicMock()
        api.label_encoder = MagicMock()
        api.label_encoder.classes_ = np.array(["BENIGN", "ATTACK"])
        api.feature_names = [f"feat_{i}" for i in range(77)]

        client = TestClient(api.app)
        response = client.post("/predict", json={
            "features": [0.0] * 77,
            "model_name": ""
        })
        assert response.status_code == 400


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
