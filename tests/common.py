from __future__ import annotations

import copy


def valid_room_scene() -> dict:
    return {
        "schema_version": "1.0",
        "scene_id": "test_scene",
        "seed": 41837,
        "units": "m",
        "entities": [
            {
                "id": "room.main",
                "kind": "room",
                "transform": {"position": [0, 0, 0], "yaw_deg": 0},
                "params": {
                    "width": 8.0,
                    "length": 10.0,
                    "height": 3.2,
                    "wall_thickness": 0.2,
                    "floor_thickness": 0.2,
                    "ceiling": True,
                    "openings": [
                        {
                            "id": "door.main",
                            "kind": "door",
                            "wall": "south",
                            "offset": 3.0,
                            "width": 1.0,
                            "height": 2.1,
                        }
                    ],
                },
            }
        ],
        "quality": {"profile": "production", "min_feature_size": 0.02},
        "output": {
            "save_blend": False,
            "blend": "test.blend",
            "report": "build-report.json",
            "manifest": "build-manifest.json",
        },
    }


def clone(value: dict) -> dict:
    return copy.deepcopy(value)

