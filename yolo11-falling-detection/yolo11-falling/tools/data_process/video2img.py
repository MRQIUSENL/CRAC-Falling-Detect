"""视频抽帧"""
import os
import cv2


def video_to_images(video_dir, output_dir, interval=10):
    """将视频每隔 interval 帧抽取一张图片"""
    for fname in os.listdir(video_dir):
        video_path = os.path.join(video_dir, fname)
        base = os.path.splitext(fname)[0]
        save_dir = os.path.join(output_dir, base)
        os.makedirs(save_dir, exist_ok=True)

        cap = cv2.VideoCapture(video_path)
        idx, frame_count = 0, 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame_count += 1
            if frame_count % interval == 0:
                cv2.imwrite(os.path.join(save_dir, f"{base}_{idx}.jpg"), frame)
                idx += 1
        cap.release()
        print(f"{fname}: {idx} 张图片")


if __name__ == "__main__":
    video_to_images("path/to/videos", "path/to/output", interval=10)
