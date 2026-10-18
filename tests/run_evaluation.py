
from app.investigator import classify_evidence


CASES = [
    {
        "name": "Daily sales import",
        "logs": [
            "Source returned only 80 rows",
            "Import ended before all expected rows were processed",
        ],
        "missing_rows": 20,
        "expected": "early_termination",
    },
    {
        "name": "Customer sync",
        "logs": [
            "Pipeline execution exceeded the 30 minute time limit",
        ],
        "missing_rows": 0,
        "expected": "timeout",
    },
    {
        "name": "Product catalog",
        "logs": [
            "Schema mismatch: price_text does not match expected numeric type",
        ],
        "missing_rows": 200,
        "expected": "schema_mismatch",
    },
    {
        "name": "Daily reporting",
        "logs": [
            "Upstream dependency failed: customer_sync",
        ],
        "missing_rows": 1000,
        "expected": "dependency_failure",
    },
]


def main():
    correct = 0

    print("\nOpsIntel AI — Diagnosis Evaluation")
    print("=" * 64)

    for case in CASES:
        predicted, hypothesis, _ = classify_evidence(
            case["logs"],
            case["missing_rows"],
        )

        passed = predicted == case["expected"]
        correct += int(passed)

        result = "PASS" if passed else "FAIL"

        print(f"\nIncident: {case['name']}")
        print(f"Expected: {case['expected']}")
        print(f"Predicted: {predicted}")
        print(f"Result: {result}")
        print(f"Hypothesis: {hypothesis}")

    total = len(CASES)
    accuracy = (correct / total) * 100

    print("\n" + "=" * 64)
    print(f"Correct diagnoses: {correct}/{total}")
    print(f"Diagnosis accuracy: {accuracy:.1f}%")
    print(
        "Scope: four predefined synthetic cases; "
        "this is not a production accuracy estimate."
    )


if __name__ == "__main__":
    main()
