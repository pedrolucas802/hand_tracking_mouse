import cv2
import numpy as np
import time
import pyautogui
import src.hand_tracking_dynamic as htd

class VirtualMouse:
    def __init__(self, wVideo=640, hVideo=480, smoothing=10, frameR=80):
        self.wVideo, self.hVideo = wVideo, hVideo
        self.wScr, self.hScr = pyautogui.size()
        self.frameR = frameR
        self.smoothing = smoothing
        self.clocx, self.clocy = 0, 0
        self.ptime = 0
        self.clicked = False
        self.mouse_enabled = True
        self.start_disable_time = None

        self.detector = htd.HandTrackingDynamic(maxHands=1)
        self.cap = self.init_camera()

    def init_camera(self):
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.wVideo)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.hVideo)
        if not cap.isOpened():
            raise RuntimeError("Cannot open camera")
        return cap

    def toggle_mouse(self, fingers):
        if all(f == 1 for f in fingers):
            if self.start_disable_time is None:
                self.start_disable_time = time.time()
            elif time.time() - self.start_disable_time > 3:
                self.mouse_enabled = not self.mouse_enabled
                print(f"Mouse {'Enabled' if self.mouse_enabled else 'Disabled'}")
                self.start_disable_time = None
        else:
            self.start_disable_time = None

    def move_cursor(self, fingers, x1, y1):
        if self.mouse_enabled and fingers[1] == 1 and all(f == 0 for f in fingers[2:]):
            index_x = np.interp(x1, (self.frameR, self.wVideo - self.frameR), (0, self.wScr))
            index_y = np.interp(y1, (self.frameR, self.hVideo - self.frameR), (0, self.hScr))

            self.clocx += (index_x - self.clocx) / self.smoothing
            self.clocy += (index_y - self.clocy) / self.smoothing

            pyautogui.moveTo(self.wScr - self.clocx, self.clocy, duration=0.05)
            return True
        return False

    def scroll_page(self, fingers, detector, frame):
        if self.mouse_enabled and fingers[1] == 1 and fingers[2] == 1 and all(f == 0 for f in fingers[3:]):
            length, frame, _ = detector.findDistance(8, 12, frame)

            scroll_speed = int(np.interp(length, (20, 150), (-10, 10)))

            if abs(scroll_speed) > 1:
                pyautogui.scroll(scroll_speed)
                return True
        return False

    def navigate_pages(self, fingers, x1):
        if self.mouse_enabled and fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 0:
            if x1 < self.wVideo // 3:
                pyautogui.hotkey("ctrl", "left")
                time.sleep(0.2)
            elif x1 > (self.wVideo * 2) // 3:
                pyautogui.hotkey("ctrl", "right")
                time.sleep(0.2)
            return True
        return False

    def detect_click(self, fingers, detector, frame):
        if self.mouse_enabled and fingers[1] == 1 and fingers[2] == 1:
            length, frame, _ = detector.findDistance(8, 12, frame)

            if length < 40 and not self.clicked:
                pyautogui.click()
                self.clicked = True
            elif length > 60:
                self.clicked = False
            return True
        return False

    def calculate_fps(self):
        ctime = time.time()
        fps = 1 / (ctime - self.ptime) if self.ptime != 0 else 0
        self.ptime = ctime
        return fps

    def run(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to grab frame")
                break

            frame = self.detector.findFingers(frame)
            lmsList, bbox = self.detector.findPosition(frame)

            if len(lmsList) != 0:
                x1, y1 = lmsList[8][1:]  # Index Finger Tip
                fingers = self.detector.findFingerUp()

                self.toggle_mouse(fingers)

                moved = self.move_cursor(fingers, x1, y1)
                scrolled = self.scroll_page(fingers, self.detector, frame)
                navigated = self.navigate_pages(fingers, x1)
                clicked = self.detect_click(fingers, self.detector, frame)

                if moved or scrolled or clicked:
                    cv2.circle(frame, (x1, y1), 15, (255, 0, 255), cv2.FILLED)

                status = "ENABLED" if self.mouse_enabled else "DISABLED"
                cv2.putText(frame, f"Mouse: {status}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

            fps = self.calculate_fps()
            cv2.putText(frame, f"FPS: {int(fps)}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            cv2.imshow("Virtual Mouse", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()
