"""图片合成视频"""
import os
import cv2


def images_to_video(image_dir, output_path, fps=30):
    """将图片序列合成为 MP4 视频"""
    images = sorted([f for f in os.listdir(image_dir) if f.endswith(".jpg")])
    if not images:
        return
    frame = cv2.imread(os.path.join(image_dir, images[0]))
    h, w = frame.shape[:2]
    writer = cv2.VideoWriter(output_path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    for img in images:
        writer.write(cv2.imread(os.path.join(image_dir, img)))
    writer.release()


if __name__ == "__main__":
    images_to_video("path/to/images", "output.mp4", fps=30)
