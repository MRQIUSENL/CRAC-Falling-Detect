"""目标追踪 + 轨迹线绘制"""
from collections import defaultdict
import cv2
import numpy as np
from ultralytics import YOLO

model = YOLO("runs/yolo11s_pretrained/train/weights/best.pt")
cap = cv2.VideoCapture("images/resources/demo.mp4")
track_history = defaultdict(lambda: [])

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    results = model.track(frame, persist=True)
    annotated = results[0].plot()

    try:
        boxes = results[0].boxes.xywh.cpu()
        track_ids = results[0].boxes.id.int().cpu().tolist()
        for box, track_id in zip(boxes, track_ids):
            x, y, w, h = box
            track = track_history[track_id]
            track.append((float(x), float(y)))
            if len(track) > 30:
                track.pop(0)
            points = np.hstack(track).astype(np.int32).reshape((-1, 1, 2))
            cv2.polylines(annotated, [points], False, (230, 230, 230), 10)
    except Exception:
        pass

    cv2.imshow("YOLO11 Tracking", annotated)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
