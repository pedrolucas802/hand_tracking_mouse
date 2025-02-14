import cv2
import numpy as np

import hand_tracking_dynamic as htd
import time
import pyautogui

######################
wVideo = 640
hVideo = 480
ctime = 0
ptime = 0
wScr, hScr = pyautogui.size()
frameR = 100  # Frame Reduction
smoothing = 7
xloc, yloc = 0, 0
clocx, clocy = 0, 0
#######################
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, wVideo)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, hVideo)
detector = htd.HandTrackingDynamic(maxHands=1)
if not cap.isOpened():
    print("Cannot open camera")
    exit()

while True:
    # 1. find  hand Landmarks
    ret, frame = cap.read()
    frame = detector.findFingers(frame)
    lmsList, bbox = detector.findPosition(frame)
    # print(lmsList)
    # 2. Get the tip of index  and middle fingers
    if len(lmsList) != 0:
        x1, y1 = lmsList[8][1:]
        x2, y2 = lmsList[12][1:]

        # print(x1,y1,x2,y2)
        # 3. check which fingers are up
        fingers = detector.findFingerUp()
        print('fingers detected', fingers)
        cv2.rectangle(frame, (frameR, frameR), (wVideo - frameR, hVideo - frameR), (255, 0, 255), 2)
        # 4. only index finger:moving mode
        if fingers[1] == 1 and fingers[2] == 0:
            # 5. Convert Coordinates
            index_x = np.interp(x1, (frameR, wVideo - frameR), (0, wScr))
            index_y = np.interp(y1, (frameR, hVideo - frameR), (0, hScr))

            # 6. Smoothen Values
            cThumbx = xloc + (index_x - xloc) / smoothing
            cThumby = yloc + (index_y - yloc) / smoothing
            # 7. Move Mouse
            pyautogui.moveTo(wScr - cThumbx, cThumby)
            cv2.circle(frame, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
            xloc, yloc = clocx, clocy
        # 8. Both Index and middle fingers are up: clicking mode
        if fingers[1] == 1 and fingers[2] == 1:
            # 9. find distance between fingers
            length, frame, lineInfo = detector.findDistance(8, 12, frame)
            # print('length', length,lineInfo)
            # 10. click mouse if distance short
            if length < 40:
                cv2.circle(frame, (lineInfo[4], lineInfo[5]),
                           15, (0, 255, 0), cv2.FILLED)
                pyautogui.click()
    # 11. frame Rate
    ctime = time.time()
    fps = 1 / (ctime - ptime)
    ptime = ctime

    cv2.putText(frame, str(int(fps)), (20, 50), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 0), 3)
    # 12. Display
    cv2.imshow('frame', frame)
    cv2.waitKey(10)