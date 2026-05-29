PYTHON = .venv/bin/python

.PHONY: env validate tables figures clean

# Create the local Python environment from the locked dependency file.
env:
	python3.10 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r environment/requirements-lock.txt

# Validate frozen artifact integrity and public threshold disclosure.
validate:
	$(PYTHON) analysis/09_validate_public_thresholds.py
	$(PYTHON) -m pytest -q tests/test_public_thresholds.py tests/test_artifact_manifest.py

# Regenerate manuscript-facing tables from frozen canonical inputs.
# No external data access required.
tables:
	$(PYTHON) analysis/13bb_build_witness_direction_table_v3.py
	$(PYTHON) analysis/13am_build_markets_comparator_paper_table_v1.py
	$(PYTHON) src/loopzero_paper/benchmarks/recommender/build_paper_facing_comparator_table.py

# Regenerate all three publication figures from frozen canonical inputs.
# No external data access required.
figures:
	$(PYTHON) src/loopzero_paper/benchmarks/recommender/generate_manuscript_artifacts.py

# Remove rendered and regenerated outputs produced by the targets above.
# Does not touch results/frozen/, results/manifests/, data/, or docs/.
clean:
	rm -f results/figures/fig*.png results/figures/fig*.pdf
	rm -f results/rendered/bridge/witness_direction_table_v3.csv
	rm -f results/rendered/bridge/witness_direction_table_v3.md
	rm -rf results/source_data/
	rm -rf results/tables/
