from __future__ import annotations

import json
import sys
from pathlib import Path

from codex_room import pbm_v4

workspace = Path(sys.argv[1])
print(json.dumps(pbm_v4.grade_battery(workspace)))
