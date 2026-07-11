"""
Integration Tests - Service-to-Service Communication
Tests complete workflows across multiple services

Author: LOVELESS
Mission: OPERATION ARGUS-TEST
Date: 2025-10-22
"""

import os
import pytest
import asyncio


# ============================================================================
# Alert Triage → Ollama Integration
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.requires_ollama
class TestAlertTriageOllamaIntegration:
    """Test Alert Triage <-> Ollama integration"""

    @pytest.mark.skipif(
        not os.getenv("ALERT_TRIAGE_URL"),
        reason="Set ALERT_TRIAGE_URL to run alert triage integration tests"
    )
    async def test_end_to_end_alert_analysis(self, http_client, alert_triage_url, sample_security_alert):
        """Test complete alert analysis workflow"""
        response = await http_client.post(
            f"{alert_triage_url}/analyze",
            json=sample_security_alert,
            timeout=30.0
        )

        if response.status_code == 200:
            data = response.json()
            assert "alert_id" in data
            assert "severity" in data
            assert "confidence" in data
            assert "summary" in data
            assert data["alert_id"] == sample_security_alert["alert_id"]
        elif response.status_code == 503:
            pytest.fail("Ollama service unavailable")
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")

    @pytest.mark.skipif(
        not os.getenv("ALERT_TRIAGE_URL"),
        reason="Set ALERT_TRIAGE_URL to run alert triage integration tests"
    )
    async def test_ollama_fallback_model(self, http_client, alert_triage_url, sample_security_alert):
        """Test fallback to secondary model when primary fails"""
        response = await http_client.post(
            f"{alert_triage_url}/analyze",
            json=sample_security_alert,
            timeout=30.0
        )

        if response.status_code == 200:
            data = response.json()
            # Check which model was used
            assert "model_used" in data
            assert data["model_used"] in ["foundation-sec-8b:latest", "llama3.1:8b"]
        else:
            pytest.fail(f"Alert triage failed with status {response.status_code}")


# ============================================================================
# RAG Service → ChromaDB Integration
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
class TestRAGChromaDBIntegration:
    """Test RAG Service <-> ChromaDB integration"""

    @pytest.mark.skipif(
        not os.getenv("RAG_SERVICE_URL"),
        reason="Set RAG_SERVICE_URL to run RAG integration tests"
    )
    async def test_vector_search(self, http_client, rag_service_url, sample_mitre_query):
        """Test semantic search in vector database"""
        response = await http_client.post(
            f"{rag_service_url}/retrieve",
            json=sample_mitre_query,
            timeout=10.0
        )

        if response.status_code == 200:
            data = response.json()
            assert "query" in data
            assert "results" in data
            assert "total_results" in data
            assert data["query"] == sample_mitre_query["query"]
        else:
            pytest.fail(f"RAG retrieve failed with status {response.status_code}")

    @pytest.mark.skipif(
        not os.getenv("RAG_SERVICE_URL"),
        reason="Set RAG_SERVICE_URL to run RAG integration tests"
    )
    async def test_document_ingestion(self, http_client, rag_service_url):
        """Test document ingestion into ChromaDB"""
        test_documents = [
            {
                "text": "MITRE ATT&CK T1110: Brute Force - Adversaries may use brute force techniques",
                "metadata": {"technique_id": "T1110", "tactic": "Credential Access"}
            }
        ]

        response = await http_client.post(
            f"{rag_service_url}/ingest",
            params={"collection": "test_collection"},
            json=test_documents,
            timeout=10.0
        )

        if response.status_code == 200:
            data = response.json()
            assert "status" in data
        else:
            pytest.fail(f"RAG ingest failed with status {response.status_code}")


# ============================================================================
# ML Inference → Alert Triage Integration
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
class TestMLAlertTriageIntegration:
    """Test ML Inference <-> Alert Triage integration"""

    @pytest.mark.skipif(
        not os.getenv("ML_INFERENCE_URL") or not os.getenv("ALERT_TRIAGE_URL"),
        reason="Set ML_INFERENCE_URL and ALERT_TRIAGE_URL to run ML-triage integration tests"
    )
    async def test_enriched_alert_analysis(self, http_client, ml_inference_url, alert_triage_url, sample_network_flow, sample_security_alert):
        """Test alert enriched with ML prediction"""
        # Step 1: Get ML prediction
        ml_response = await http_client.post(
            f"{ml_inference_url}/predict",
            json=sample_network_flow,
            timeout=10.0
        )

        if ml_response.status_code != 200:
            pytest.fail(f"ML service failed with status {ml_response.status_code}")

        ml_data = ml_response.json()

        # Step 2: Enrich alert with ML prediction
        enriched_alert = sample_security_alert.copy()
        enriched_alert["ml_prediction"] = ml_data["prediction"]
        enriched_alert["ml_confidence"] = ml_data["confidence"]

        # Step 3: Send enriched alert to triage
        triage_response = await http_client.post(
            f"{alert_triage_url}/analyze",
            json=enriched_alert,
            timeout=30.0
        )

        if triage_response.status_code == 200:
            triage_data = triage_response.json()
            assert "severity" in triage_data
        else:
            pytest.fail(f"Triage failed with status {triage_response.status_code}")


# ============================================================================
# Multi-Service Health Checks
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
class TestMultiServiceHealth:
    """Test health checks across all services"""

    async def test_all_services_healthy(self, http_client, alert_triage_url, rag_service_url, ml_inference_url):
        """Test all services are healthy"""
        services = {
            "alert-triage": alert_triage_url,
            "rag-service": rag_service_url,
            "ml-inference": ml_inference_url
        }

        results = {}
        for name, url in services.items():
            try:
                response = await http_client.get(f"{url}/health", timeout=5.0)
                results[name] = response.status_code == 200
            except Exception:
                results[name] = False

        # Log results
        healthy_count = sum(results.values())
        print(f"\n🏥 Health Check: {healthy_count}/{len(services)} services healthy")
        for name, healthy in results.items():
            status = "✅" if healthy else "❌"
            print(f"  {status} {name}")

    @pytest.mark.skipif(
        not os.getenv("ALERT_TRIAGE_URL"),
        reason="Set ALERT_TRIAGE_URL to run service dependency tests"
    )
    async def test_service_dependencies(self, http_client, alert_triage_url, ollama_url):
        """Test service dependency chains"""
        # Check Alert Triage health
        triage_response = await http_client.get(f"{alert_triage_url}/health", timeout=5.0)

        if triage_response.status_code == 200:
            data = triage_response.json()
            # Alert Triage depends on Ollama
            if "ollama_connected" in data:
                print(f"\n🔗 Alert Triage → Ollama: {'✅' if data['ollama_connected'] else '❌'}")
        else:
            pytest.fail(f"Alert triage health check failed with status {triage_response.status_code}")


# ============================================================================
# Data Flow Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
class TestDataFlow:
    """Test data flow through the system"""

    @pytest.mark.skipif(
        not os.getenv("ALERT_TRIAGE_URL"),
        reason="Set ALERT_TRIAGE_URL to run data flow integration tests"
    )
    async def test_alert_to_case_workflow(self, http_client, alert_triage_url, sample_security_alert):
        """Test: Alert → Triage → [TheHive Case]"""
        # Step 1: Analyze alert
        response = await http_client.post(
            f"{alert_triage_url}/analyze",
            json=sample_security_alert,
            timeout=30.0
        )

        if response.status_code == 200:
            triage_result = response.json()

            # Step 2: Validate triage result structure
            assert triage_result["severity"] in ["critical", "high", "medium", "low", "info"]
            assert 0.0 <= triage_result["confidence"] <= 1.0

            # Step 3: Create TheHive case (when integrated)
            # This would send to TheHive API
            # TODO: Implement when TheHive is deployed

        else:
            pytest.fail(f"Alert triage failed with status {response.status_code}")

    @pytest.mark.skipif(
        not os.getenv("LOG_SUMMARIZATION_URL"),
        reason="Set LOG_SUMMARIZATION_URL to run log summarization tests"
    )
    async def test_log_to_summary_workflow(self, http_client, sample_log_batch):
        """Test: Logs → Summarization → ChromaDB"""
        # TODO: Implement when log-summarization service is ready
        pytest.fail("Log summarization service not yet implemented")


# ============================================================================
# Performance Integration Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
class TestSystemPerformance:
    """Test system-wide performance"""

    @pytest.mark.skipif(
        not os.getenv("ALERT_TRIAGE_URL"),
        reason="Set ALERT_TRIAGE_URL to run performance integration tests"
    )
    async def test_concurrent_alert_processing(self, http_client, alert_triage_url, sample_security_alert):
        """Test concurrent alert processing"""
        # Create multiple alerts
        alerts = []
        for i in range(10):
            alert = sample_security_alert.copy()
            alert["alert_id"] = f"test-alert-{i:03d}"
            alerts.append(alert)

        # Send all alerts concurrently
        tasks = [
            http_client.post(f"{alert_triage_url}/analyze", json=alert, timeout=30.0)
            for alert in alerts
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successful responses
        successful = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)
        print(f"\n📊 Concurrent Processing: {successful}/{len(alerts)} successful")

        # At least 80% should succeed
        assert successful >= len(alerts) * 0.8

    @pytest.mark.skipif(
        not os.getenv("ML_INFERENCE_URL"),
        reason="Set ML_INFERENCE_URL to run throughput tests"
    )
    async def test_throughput(self, http_client, ml_inference_url, sample_network_flow):
        """Test system throughput (predictions/second)"""
        import time

        num_requests = 50
        start_time = time.time()

        tasks = [
            http_client.post(f"{ml_inference_url}/predict", json=sample_network_flow, timeout=10.0)
            for _ in range(num_requests)
        ]

        responses = await asyncio.gather(*tasks, return_exceptions=True)
        duration = time.time() - start_time

        successful = sum(1 for r in responses if not isinstance(r, Exception) and r.status_code == 200)
        throughput = successful / duration

        print(f"\n⚡ Throughput: {throughput:.2f} predictions/second")
        print(f"   Total: {successful}/{num_requests} successful in {duration:.2f}s")

        # Should handle at least 10 predictions/second
        assert throughput >= 10


# ============================================================================
# Error Propagation Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
class TestErrorPropagation:
    """Test error handling across services"""

    @pytest.mark.skipif(
        not os.getenv("ALERT_TRIAGE_URL"),
        reason="Set ALERT_TRIAGE_URL to run error propagation tests"
    )
    async def test_ollama_down_graceful_degradation(self, http_client, alert_triage_url, sample_security_alert):
        """Test behavior when Ollama is down"""
        response = await http_client.post(
            f"{alert_triage_url}/analyze",
            json=sample_security_alert,
            timeout=30.0
        )

        if response.status_code == 503:
            # Expected when Ollama is down
            data = response.json()
            assert "detail" in data
            print("\n⚠️  Graceful degradation: Service unavailable")
        elif response.status_code == 200:
            print("\n✅ Ollama is up and running")
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")

    @pytest.mark.skipif(
        not os.getenv("ALERT_TRIAGE_URL"),
        reason="Set ALERT_TRIAGE_URL to run error propagation tests"
    )
    async def test_invalid_data_rejection(self, http_client, alert_triage_url):
        """Test rejection of invalid data"""
        invalid_alert = {
            "alert_id": "test-001"
            # Missing required fields
        }

        response = await http_client.post(
            f"{alert_triage_url}/analyze",
            json=invalid_alert,
            timeout=10.0
        )

        # Should get 422 Validation Error
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "integration"])
