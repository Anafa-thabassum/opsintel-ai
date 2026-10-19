import json
from pathlib import Path

from scripts.import_orchestrator_json import normalize_export


ROOT = Path(__file__).resolve().parents[1]


def test_airflow_export_normalizes_to_opsintel_records():
    payload = json.loads(
        (ROOT / "examples/integrations/airflow_dag_runs.json").read_text()
    )

    result = normalize_export("airflow", payload)

    assert result[0]["run_id"] == 3001
    assert result[0]["status"] == "FAILED"
    assert result[0]["actual_rows"] == 812
    assert result[0]["source"] == "airflow"


def test_dbt_export_uses_adapter_row_count_and_expected_rows():
    payload = json.loads(
        (ROOT / "examples/integrations/dbt_run_results.json").read_text()
    )

    result = normalize_export("dbt", payload)

    assert result[0]["run_id"] == 3002
    assert result[0]["pipeline_name"] == "model.analytics.customer_profile"
    assert result[0]["expected_rows"] == 200
    assert result[0]["actual_rows"] == 0
