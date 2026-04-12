from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np


@dataclass
class TrackState:
    smoothed: np.ndarray
    missing_frames: int = 0


class SimpleTracker:
    def __init__(self, alpha: float = 0.65, max_missing: int = 10) -> None:
        self.alpha = alpha
        self.max_missing = max_missing
        self.tracks: Dict[int, TrackState] = {}
        self.boxes: Dict[int, Tuple[int, int, int, int]] = {}
        self.next_track_id = 1

    def update(self, boxes: List[Tuple[int, int, int, int]], probabilities: List[List[float]]) -> List[Tuple[int, List[float]]]:
        assignments = self._assign_tracks(boxes)
        seen_ids = set()
        output: List[Tuple[int, List[float]]] = []

        for index, track_id in assignments.items():
            probs = np.asarray(probabilities[index], dtype=np.float32)
            state = self.tracks.get(track_id)
            if state is None:
                state = TrackState(smoothed=probs)
            else:
                state.smoothed = self.alpha * probs + (1.0 - self.alpha) * state.smoothed
                state.missing_frames = 0
            self.tracks[track_id] = state
            self.boxes[track_id] = boxes[index]
            seen_ids.add(track_id)
            output.append((track_id, state.smoothed.tolist()))

        for track_id in list(self.tracks):
            if track_id not in seen_ids:
                self.tracks[track_id].missing_frames += 1
                if self.tracks[track_id].missing_frames > self.max_missing:
                    self.tracks.pop(track_id, None)
                    self.boxes.pop(track_id, None)

        return output

    def _assign_tracks(self, boxes: List[Tuple[int, int, int, int]]) -> Dict[int, int]:
        assignments: Dict[int, int] = {}
        available = set(self.boxes.keys())
        for index, box in enumerate(boxes):
            best_track = None
            best_score = 0.0
            for track_id in list(available):
                score = self._iou(box, self.boxes[track_id])
                if score > best_score:
                    best_score = score
                    best_track = track_id
            if best_track is not None and best_score > 0.2:
                assignments[index] = best_track
                available.remove(best_track)
            else:
                assignments[index] = self.next_track_id
                self.next_track_id += 1
        return assignments

    def _iou(self, box_a: Tuple[int, int, int, int], box_b: Tuple[int, int, int, int]) -> float:
        ax1, ay1, ax2, ay2 = box_a
        bx1, by1, bx2, by2 = box_b
        inter_x1 = max(ax1, bx1)
        inter_y1 = max(ay1, by1)
        inter_x2 = min(ax2, bx2)
        inter_y2 = min(ay2, by2)
        inter_w = max(0, inter_x2 - inter_x1)
        inter_h = max(0, inter_y2 - inter_y1)
        inter_area = inter_w * inter_h
        area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
        area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
        denom = area_a + area_b - inter_area
        return inter_area / denom if denom else 0.0

