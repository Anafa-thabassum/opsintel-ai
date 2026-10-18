
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
    {
        "name": "Billing export deadline",
        "logs": ["Execution deadline exceeded after 900 seconds"],
        "missing_rows": 0,
        "expected": "timeout",
    },
    {
        "name": "Inventory worker timeout",
        "logs": ["Worker timed out while waiting for a warehouse slot"],
        "missing_rows": 0,
        "expected": "timeout",
    },
    {
        "name": "Orders invalid cast",
        "logs": ["Invalid cast from VARCHAR to DECIMAL for order_total"],
        "missing_rows": 12,
        "expected": "schema_mismatch",
    },
    {
        "name": "Customer type conversion",
        "logs": ["Type conversion failed for customer_birth_date"],
        "missing_rows": 8,
        "expected": "schema_mismatch",
    },
    {
        "name": "Reporting prerequisite",
        "logs": ["Prerequisite task failed: aggregate_sales"],
        "missing_rows": 500,
        "expected": "dependency_failure",
    },
    {
        "name": "Warehouse dependency",
        "logs": ["Dependency failed before warehouse refresh began"],
        "missing_rows": 900,
        "expected": "dependency_failure",
    },
    {
        "name": "Payments aborted",
        "logs": ["Load aborted before completion after batch 14"],
        "missing_rows": 35,
        "expected": "early_termination",
    },
    {
        "name": "Events stopped early",
        "logs": ["Processing stopped early after a worker exited"],
        "missing_rows": 70,
        "expected": "early_termination",
    },
    {
        "name": "Orders row shortfall",
        "logs": ["Row shortfall detected in source extract"],
        "missing_rows": 44,
        "expected": "incomplete_data",
    },
    {
        "name": "Products incomplete extract",
        "logs": ["Source contained fewer rows than expected"],
        "missing_rows": 15,
        "expected": "incomplete_data",
    },
    {
        "name": "Unknown worker exit",
        "logs": ["Worker exited with code 71; no diagnostic details"],
        "missing_rows": 0,
        "expected": "unclassified",
    },
    {
        "name": "Benign timeout configuration",
        "logs": ["Timeout threshold configured at 30 minutes"],
        "missing_rows": 0,
        "expected": "unclassified",
    },
]


def main():
    correct = 0
    category_results = {}

    print("\nOpsIntel AI — Diagnosis Evaluation")
    print("=" * 64)

    for case in CASES:
        predicted, hypothesis, _ = classify_evidence(
            case["logs"],
            case["missing_rows"],
        )

        passed = predicted == case["expected"]
        correct += int(passed)
        category = category_results.setdefault(
            case["expected"],
            {"correct": 0, "total": 0},
        )
        category["correct"] += int(passed)
        category["total"] += 1

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
    print("Per-category accuracy:")
    for category, result in sorted(category_results.items()):
        print(
            f"  {category}: {result['correct']}/{result['total']}"
        )
    print(
        f"Scope: {total} predefined synthetic challenge cases; "
        "this is not a production accuracy estimate."
    )


if __name__ == "__main__":
    main()
