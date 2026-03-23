import cv2
from MPVStream import MPVStream

url = "https://open.ys7.com/v3/openlive/FR3098735_1_2.m3u8?expire=1799307668&id=930848885066555392&t=acfcf2b5652add9dfa2239bd5b386ae5b808aace4dad6c0aac1a0168448b4113&ev=101&supportH265=1"
s = MPVStream(url, target_fps=15)

for i in range(200):
    ok, frame = s.read()
    if ok:
        cv2.imwrite("debug_frame.jpg", frame)
        print("saved debug_frame.jpg", frame.shape)
        break

s.release()
