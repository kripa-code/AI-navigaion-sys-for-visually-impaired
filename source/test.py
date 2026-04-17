import cv2

cap = cv2.VideoCapture("http://10.22.64.179:4747/video")

while True:
    ret, frame = cap.read()
    print(ret)

    if ret:
        cv2.imshow("Test", frame)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()