import json
from pathlib import Path
# JSON is a YAML subset; no parser dependency needed.
RULES = json.loads(Path(__file__).with_name('rules.yaml').read_text())
