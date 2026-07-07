"""图片合成视频 (同 img2video)"""
from img2video import images_to_video

if __name__ == "__main__":
    images_to_video("path/to/images", "output.mp4", fps=10)
