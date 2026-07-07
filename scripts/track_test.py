"""目标追踪测试 (BoT-SORT / ByteTrack)"""
import cv2
from ultralytics import YOLO

model = YOLO("yolo11n.pt")
cap = cv2.VideoCapture("images/resources/demo.mp4")

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break
    results = model.track(frame, persist=True, tracker="botsort.yaml")
    cv2.imshow("YOLO11 Tracking", results[0].plot())
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
