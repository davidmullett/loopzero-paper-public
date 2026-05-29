from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


BENCHMARK_ID = "movielens25m_recursive_frontier_public_v1"
CONTRACT_FILENAME = f"{BENCHMARK_ID}__contract_freeze.json"
AUDIT_JSON_FILENAME = f"{BENCHMARK_ID}__engine_audit_report.json"
AUDIT_MD_FILENAME = f"{BENCHMARK_ID}__engine_audit_report.md"


# ============================================================
# Paths
# ============================================================

@dataclass(frozen=True)
class RepoPaths:
    repo_root: Path
    results_frozen: Path
    results_manifests: Path
    recommender_dir: Path
    contract_path: Path
    manifest_builder_path: Path


def build_repo_paths(repo_root: Path) -> RepoPaths:
    recommender_dir = repo_root / "src" / "loopzero_paper" / "benchmarks" / "recommender"
    results_frozen = repo_root / "results" / "frozen"
    results_manifests = repo_root / "results" / "manifests"
    return RepoPaths(
        repo_root=repo_root,
        results_frozen=results_frozen,
        results_manifests=results_manifests,
        recommender_dir=recommender_dir,
        contract_path=results_frozen / CONTRACT_FILENAME,
        manifest_builder_path=recommender_dir / "build_user_episode_manifest.py",
    )


# ============================================================
# JSON helpers
# ============================================================

def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ============================================================
# Contract extraction
# ============================================================

def load_contract_engine(paths: RepoPaths) -> Dict[str, Any]:
    if not paths.contract_path.exists():
        raise FileNotFoundError(
            f"Missing contract freeze: {paths.contract_path}\n"
            f"Run freeze_contract.py first."
        )
    contract = load_json(paths.contract_path)
    if contract.get("benchmark_id") != BENCHMARK_ID:
        raise ValueError(
            f"Unexpected benchmark_id in contract: {contract.get('benchmark_id')!r}"
        )
    engine = contract.get("engine")
    if not isinstance(engine, dict):
        raise ValueError("Contract is missing engine block.")
    return contract


# ============================================================
# AST inspection of build_user_episode_manifest.py
# ============================================================

class SourceInspector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.class_names: List[str] = []
        self.function_names: List[str] = []
        self.engine_family_literals: List[str] = []
        self.recommend_method_found: bool = False
        self.top_neighbor_method_found: bool = False
        self.choose_frontier_hit_found: bool = False
        self.sort_keys_seen: List[Tuple[str, ...]] = []
        self.uses_global_popularity_fallback: bool = False
        self.uses_exclude_seen_items: bool = False
        self.uses_weighted_sum_scores: bool = False
        self.uses_cosine_comment_or_literal: bool = False
        self.uses_neighborhood_size_attr: bool = False
        self.uses_min_common_raters_attr: bool = False
        self.tie_break_literals: List[str] = []
        self.freeze_engine_class_name: Optional[str] = None

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
        self.class_names.append(node.name)
        if node.name == "FrozenItemItemCFEngine":
            self.freeze_engine_class_name = node.name
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        self.function_names.append(node.name)
        if node.name == "recommend":
            self.recommend_method_found = True
        if node.name == "_top_neighbors":
            self.top_neighbor_method_found = True
        if node.name == "choose_frontier_hit":
            self.choose_frontier_hit_found = True
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> Any:
        if isinstance(node.value, str):
            if node.value == "item_item_collaborative_filtering":
                self.engine_family_literals.append(node.value)
            if node.value == "score_desc_then_movieId_asc":
                self.tie_break_literals.append(node.value)
            if "cosine" in node.value.lower():
                self.uses_cosine_comment_or_literal = True
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> Any:
        # detect sort key tuples / lists
        try:
            value = ast.literal_eval(node.value)
            if isinstance(value, (tuple, list)):
                vals = tuple(str(x) for x in value)
                if vals:
                    self.sort_keys_seen.append(vals)
        except Exception:
            pass
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> Any:
        # score accumulation heuristic
        if isinstance(node.target, ast.Subscript) and isinstance(node.op, ast.Add):
            self.uses_weighted_sum_scores = True
        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare) -> Any:
        src = ast.unparse(node) if hasattr(ast, "unparse") else ""
        if "seen_items" in src:
            self.uses_exclude_seen_items = True
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> Any:
        if node.attr == "neighborhood_size":
            self.uses_neighborhood_size_attr = True
        if node.attr == "min_common_raters":
            self.uses_min_common_raters_attr = True
        if node.attr == "_global_popularity":
            self.uses_global_popularity_fallback = True
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> Any:
        if node.id == "_global_popularity" or node.id == "global_popularity":
            self.uses_global_popularity_fallback = True
        self.generic_visit(node)


def inspect_manifest_builder(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"Manifest builder not found: {path}\n"
            f"Create build_user_episode_manifest.py first."
        )

    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    inspector = SourceInspector()
    inspector.visit(tree)

    return {
        "path": str(path),
        "sha256": sha256_text(source),
        "class_names": sorted(set(inspector.class_names)),
        "function_names": sorted(set(inspector.function_names)),
        "freeze_engine_class_name": inspector.freeze_engine_class_name,
        "recommend_method_found": inspector.recommend_method_found,
        "top_neighbor_method_found": inspector.top_neighbor_method_found,
        "choose_frontier_hit_found": inspector.choose_frontier_hit_found,
        "engine_family_literals": sorted(set(inspector.engine_family_literals)),
        "tie_break_literals": sorted(set(inspector.tie_break_literals)),
        "sort_keys_seen": sorted(set(inspector.sort_keys_seen)),
        "uses_global_popularity_fallback": inspector.uses_global_popularity_fallback,
        "uses_exclude_seen_items": inspector.uses_exclude_seen_items,
        "uses_weighted_sum_scores": inspector.uses_weighted_sum_scores,
        "uses_cosine_comment_or_literal": inspector.uses_cosine_comment_or_literal,
        "uses_neighborhood_size_attr": inspector.uses_neighborhood_size_attr,
        "uses_min_common_raters_attr": inspector.uses_min_common_raters_attr,
    }


# ============================================================
# Audit logic
# ============================================================

def audit_engine_alignment(contract: Dict[str, Any], impl: Dict[str, Any]) -> Dict[str, Any]:
    engine = contract["engine"]
    hyper = engine.get("hyperparameters", {})

    checks: List[Dict[str, Any]] = []

    def add_check(name: str, passed: bool, expected: Any, observed: Any, severity: str = "error") -> None:
        checks.append({
            "name": name,
            "passed": passed,
            "expected": expected,
            "observed": observed,
            "severity": severity,
        })

    add_check(
        "engine_family_matches_supported_builder",
        engine.get("engine_family") == "item_item_collaborative_filtering"
        and "item_item_collaborative_filtering" in impl["engine_family_literals"],
        "contract engine_family=item_item_collaborative_filtering and same literal enforced in builder",
        {
            "contract_engine_family": engine.get("engine_family"),
            "builder_engine_family_literals": impl["engine_family_literals"],
        },
    )

    add_check(
        "frozen_engine_class_present",
        impl["freeze_engine_class_name"] == "FrozenItemItemCFEngine",
        "FrozenItemItemCFEngine class exists",
        impl["freeze_engine_class_name"],
    )

    add_check(
        "recommend_method_present",
        impl["recommend_method_found"],
        True,
        impl["recommend_method_found"],
    )

    add_check(
        "neighbor_method_present",
        impl["top_neighbor_method_found"],
        True,
        impl["top_neighbor_method_found"],
    )

    add_check(
        "exclude_seen_items_policy_present",
        engine.get("candidate_policy") == "exclude_seen_items_then_rank_all_remaining_items"
        and impl["uses_exclude_seen_items"],
        {
            "contract_candidate_policy": "exclude_seen_items_then_rank_all_remaining_items",
            "builder_behavior": "exclude seen items in recommend()",
        },
        {
            "contract_candidate_policy": engine.get("candidate_policy"),
            "builder_detected_exclude_seen_items": impl["uses_exclude_seen_items"],
        },
    )

    add_check(
        "weighted_sum_score_aggregation_present",
        hyper.get("score_aggregation") == "weighted_sum"
        and impl["uses_weighted_sum_scores"],
        {
            "contract_score_aggregation": "weighted_sum",
            "builder_behavior": "score accumulation with +=",
        },
        {
            "contract_score_aggregation": hyper.get("score_aggregation"),
            "builder_detected_weighted_sum": impl["uses_weighted_sum_scores"],
        },
    )

    add_check(
        "cosine_similarity_present",
        hyper.get("similarity") == "cosine" and impl["uses_cosine_comment_or_literal"],
        {
            "contract_similarity": "cosine",
            "builder_behavior": "cosine literal/comment present in engine implementation",
        },
        {
            "contract_similarity": hyper.get("similarity"),
            "builder_detected_cosine_literal": impl["uses_cosine_comment_or_literal"],
        },
        severity="warning",
    )

    add_check(
        "neighborhood_size_hyperparameter_present",
        "neighborhood_size" in hyper and impl["uses_neighborhood_size_attr"],
        {
            "contract_hyperparameter": "neighborhood_size",
            "builder_behavior": "uses self.neighborhood_size",
        },
        {
            "contract_neighborhood_size": hyper.get("neighborhood_size"),
            "builder_detected_attr": impl["uses_neighborhood_size_attr"],
        },
    )

    add_check(
        "min_common_raters_hyperparameter_present",
        "min_common_raters" in hyper and impl["uses_min_common_raters_attr"],
        {
            "contract_hyperparameter": "min_common_raters",
            "builder_behavior": "uses self.min_common_raters",
        },
        {
            "contract_min_common_raters": hyper.get("min_common_raters"),
            "builder_detected_attr": impl["uses_min_common_raters_attr"],
        },
    )

    add_check(
        "global_popularity_fallback_detected",
        impl["uses_global_popularity_fallback"],
        "Builder contains deterministic popularity fallback",
        impl["uses_global_popularity_fallback"],
        severity="warning",
    )

    add_check(
        "tie_break_literal_present",
        engine.get("tie_break_rule") in impl["tie_break_literals"],
        {"contract_tie_break_rule": engine.get("tie_break_rule")},
        {"builder_tie_break_literals": impl["tie_break_literals"]},
    )

    add_check(
        "deterministic_flag_true",
        bool(engine.get("deterministic")) is True,
        True,
        engine.get("deterministic"),
    )

    add_check(
        "engine_hash_present",
        isinstance(engine.get("engine_hash"), str) and len(engine.get("engine_hash")) > 0,
        "non-empty engine_hash",
        engine.get("engine_hash"),
    )

    hard_failures = [c for c in checks if (not c["passed"] and c["severity"] == "error")]
    warnings = [c for c in checks if (not c["passed"] and c["severity"] == "warning")]

    placeholder_signals: List[str] = []
    notes = str(engine.get("notes", "") or "").lower()
    if "replace this engine spec" in notes:
        placeholder_signals.append("engine notes contain 'Replace this engine spec'")
    if "placeholder" in notes:
        placeholder_signals.append("engine notes contain 'placeholder'")
    if engine.get("code_commit") in (None, "", "null"):
        placeholder_signals.append("engine code_commit is missing/null")

    decision = "PASS"
    if hard_failures:
        decision = "FAIL"
    elif placeholder_signals or warnings:
        decision = "REVIEW_REQUIRED"

    return {
        "benchmark_id": contract["benchmark_id"],
        "contract_sha256": contract.get("contract_sha256"),
        "engine_hash": engine.get("engine_hash"),
        "contract_engine_block": engine,
        "implementation_inspection": impl,
        "checks": checks,
        "hard_failure_count": len(hard_failures),
        "warning_count": len(warnings),
        "placeholder_signals": placeholder_signals,
        "decision": decision,
        "recommended_action": recommended_action(decision, placeholder_signals, hard_failures),
    }


def recommended_action(
    decision: str,
    placeholder_signals: List[str],
    hard_failures: List[Dict[str, Any]],
) -> str:
    if decision == "FAIL":
        return (
            "Do not run Gate 1. Fix the engine/implementation mismatch, then regenerate "
            "Step 1 (contract freeze), Step 2 (provenance if needed), and Step 3 (manifest)."
        )
    if decision == "REVIEW_REQUIRED":
        return (
            "Do not treat the benchmark as manuscript-final yet. Either explicitly declare "
            "the current deterministic item-item CF engine as canonical, or replace the "
            "engine spec and regenerate Steps 1-3 before Gate 1."
        )
    return (
        "Engine audit passes structural checks. You may proceed to Gate 1 if you are "
        "comfortable naming this exact engine in Methods."
    )


# ============================================================
# Rendering
# ============================================================

def render_markdown(report: Dict[str, Any]) -> str:
    engine = report["contract_engine_block"]
    impl = report["implementation_inspection"]

    lines: List[str] = []
    lines.append(f"# Engine Audit Report — {report['benchmark_id']}")
    lines.append("")
    lines.append(f"**Decision:** `{report['decision']}`")
    lines.append("")
    lines.append(f"**Recommended action:** {report['recommended_action']}")
    lines.append("")
    lines.append("## Frozen engine contract")
    lines.append("")
    lines.append(f"- engine_family: `{engine.get('engine_family')}`")
    lines.append(f"- engine_name: `{engine.get('engine_name')}`")
    lines.append(f"- engine_version: `{engine.get('engine_version')}`")
    lines.append(f"- deterministic: `{engine.get('deterministic')}`")
    lines.append(f"- candidate_policy: `{engine.get('candidate_policy')}`")
    lines.append(f"- update_policy: `{engine.get('update_policy')}`")
    lines.append(f"- tie_break_rule: `{engine.get('tie_break_rule')}`")
    lines.append(f"- engine_hash: `{engine.get('engine_hash')}`")
    lines.append(f"- code_commit: `{engine.get('code_commit')}`")
    lines.append("")
    lines.append("### Hyperparameters")
    lines.append("")
    for k, v in sorted(engine.get("hyperparameters", {}).items()):
        lines.append(f"- {k}: `{v}`")
    lines.append("")
    lines.append("## Implementation inspection")
    lines.append("")
    lines.append(f"- source path: `{impl['path']}`")
    lines.append(f"- source sha256: `{impl['sha256']}`")
    lines.append(f"- engine class found: `{impl['freeze_engine_class_name']}`")
    lines.append(f"- recommend() found: `{impl['recommend_method_found']}`")
    lines.append(f"- _top_neighbors() found: `{impl['top_neighbor_method_found']}`")
    lines.append(f"- choose_frontier_hit() found: `{impl['choose_frontier_hit_found']}`")
    lines.append(f"- engine family literals: `{impl['engine_family_literals']}`")
    lines.append(f"- tie-break literals: `{impl['tie_break_literals']}`")
    lines.append(f"- uses exclude_seen_items: `{impl['uses_exclude_seen_items']}`")
    lines.append(f"- uses weighted_sum scoring: `{impl['uses_weighted_sum_scores']}`")
    lines.append(f"- uses cosine literal/comment: `{impl['uses_cosine_comment_or_literal']}`")
    lines.append(f"- uses neighborhood_size attr: `{impl['uses_neighborhood_size_attr']}`")
    lines.append(f"- uses min_common_raters attr: `{impl['uses_min_common_raters_attr']}`")
    lines.append(f"- uses global popularity fallback: `{impl['uses_global_popularity_fallback']}`")
    lines.append("")
    lines.append("## Check results")
    lines.append("")
    for check in report["checks"]:
        icon = "✅" if check["passed"] else ("⚠️" if check["severity"] == "warning" else "❌")
        lines.append(f"- {icon} **{check['name']}**")
        if not check["passed"]:
            lines.append(f"  - expected: `{check['expected']}`")
            lines.append(f"  - observed: `{check['observed']}`")
    lines.append("")
    lines.append("## Placeholder signals")
    lines.append("")
    if report["placeholder_signals"]:
        for s in report["placeholder_signals"]:
            lines.append(f"- ⚠️ {s}")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines) + "\n"


# ============================================================
# Main
# ============================================================

def run(repo_root: Path) -> Tuple[Path, Path]:
    paths = build_repo_paths(repo_root)
    contract = load_contract_engine(paths)
    impl = inspect_manifest_builder(paths.manifest_builder_path)
    report = audit_engine_alignment(contract, impl)

    paths.results_manifests.mkdir(parents=True, exist_ok=True)

    json_path = paths.results_manifests / AUDIT_JSON_FILENAME
    md_path = paths.results_manifests / AUDIT_MD_FILENAME

    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")

    print(f"[ok] wrote audit JSON: {json_path}")
    print(f"[ok] wrote audit MD:   {md_path}")
    print(f"[ok] decision:         {report['decision']}")
    print(f"[ok] recommended:      {report['recommended_action']}")
    return json_path, md_path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    run(repo_root)


if __name__ == "__main__":
    main()