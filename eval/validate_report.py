"""Check whether an LLM-judge report is complete enough to publish.

This is a local, zero-credit structural check. It does not validate judge quality.
"""

import json
import sys
from pathlib import Path


def validate(report):
    errors = []
    evaluations = report.get("evaluations", [])
    if not evaluations:
        return ["No document evaluations found."]
    for item in evaluations:
        name = item.get("document", "<unnamed>")
        metrics = item.get("metrics", {})
        details = item.get("details", [])
        generated = metrics.get("total_questions", 0)
        evaluated = metrics.get("evaluated_questions", len(details))
        if not details:
            errors.append(f"{name}: no per-question details")
        if evaluated != len(details):
            errors.append(f"{name}: evaluated count does not match details")
        if generated != evaluated:
            errors.append(f"{name}: {generated} generated, {evaluated} evaluated")
        for metric in ("faithfulness_score", "relevancy_score"):
            value = metrics.get(metric)
            if value is None or not 0 <= value <= 1:
                errors.append(f"{name}: missing or invalid {metric}")
    return errors


if __name__ == "__main__":
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "eval/eval_results.json")
    issues = validate(json.loads(path.read_text()))
    if issues:
        for issue in issues:
            print("INCOMPLETE:", issue)
        sys.exit(1)
    print("Report has complete per-question fields. Review labels and methodology before publishing.")
