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

    def _apply_nested_orders(self, data: Any, orders: dict[str, list[str]]):
        # Reorder known lists/dicts by the provided field order
        if isinstance(data, dict):
            for key, value in list(data.items()):
                if key in orders:
                    # Reorder items inside list/dict by order
                    order = orders[key]
                    if isinstance(value, list):
                        new_list = []
                        for el in value:
                            if isinstance(el, dict):
                                ordered = OrderedDict()
                                for k in order:
                                    if k in el:
                                        ordered[k] = el[k]
                                for k in sorted(k for k in el.keys() if k not in order):
                                    ordered[k] = el[k]
                                new_list.append(ordered)
                            else:
                                new_list.append(el)
                        data[key] = new_list
                    elif isinstance(value, dict):
                        ordered = OrderedDict()
                        for k in order:
                            if k in value:
                                ordered[k] = value[k]
                        for k in sorted(k for k in value.keys() if k not in order):
                            ordered[k] = value[k]
                        data[key] = ordered
                # Recurse into children
                self._apply_nested_orders(value, orders)
        elif isinstance(data, list):
            for el in data:
                self._apply_nested_orders(el, orders)

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        classe = adapter.get("classe")
        processo_id = adapter.get("processo_id")
        filename = None
        if classe and processo_id:
            filename = f"{classe}_{processo_id}.json"

        template = None
        if filename:
            template = self._find_gt(filename)

        # 0) Apply full nested template first (strict global ordering)
        try:
            full_template = spider.settings.get("NESTED_TEMPLATE")
        except Exception:
            full_template = None
        if isinstance(full_template, dict):
            data = adapter.asdict()
            strict = reorder_with_template(full_template, data)
            for k in list(adapter.keys()):
                del adapter[k]
            for k, v in strict.items():
                adapter[k] = v

        # 1) Apply global nested field order templates
        try:
            orders = spider.settings.getdict("NESTED_FIELD_ORDERS")
        except Exception:
            orders = {}
        if orders:
            self._apply_nested_orders(adapter.asdict(), orders)

        # 2) If a file-specific ground-truth exists, use it to refine nested order further
        if template is not None:
            tmpl = template[0] if isinstance(template, list) and template else template
            data = adapter.asdict()
            reordered = reorder_with_template(tmpl, data)
            # Replace keys deterministically
            for k in list(adapter.keys()):
                del adapter[k]
            for k, v in reordered.items():
                adapter[k] = v

        return item
