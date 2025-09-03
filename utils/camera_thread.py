import os
import time
import re

from PyQt5.QtCore import (QIODevice, QByteArray, QObject, QThread, pyqtSignal,
                          pyqtSlot, QMutex, QTimer)
from PyQt5.QtGui import QImage
import cv2
import numpy as np


def find_points(img, draw_img):
    detect_img = img.copy()
    # detect_img = cv2.GaussianBlur(detect_img, (5, 5), 0)
    # detect_img = cv2.resize(detect_img, (detect_img.shape[1]//2, detect_img.shape[0]//2))
    thresh = cv2.threshold(detect_img, 100, 255, cv2.THRESH_BINARY)[1]

    kernel = np.ones((3, 3), np.uint8)
    # thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)

    coutours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
    bright_spots = []
    circularity_threshold, aspect_ratio_threshold = 0.3, 0.7
    for contour in coutours:
        area = cv2.contourArea(contour)
        if 20 > area > 6:
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])

                perimeter = cv2.arcLength(contour, True)
                circularity = 4 * np.pi * area / (
                    perimeter * perimeter) if perimeter > 0 else 0
                _, _, w, h = cv2.boundingRect(contour)
                aspect_ratio = min(w, h) / max(w, h) if max(w, h) > 0 else 0

                print(
                    f"circularity: {circularity}, aspect_ratio: {aspect_ratio}"
                )
                if circularity > circularity_threshold and aspect_ratio > aspect_ratio_threshold:
                    bright_spots.append((cX, cY))
                    cv2.circle(draw_img, (cX, cY), 2, (255, 0, 255), -1)

    return bright_spots, detect_img, thresh


class CameraWorker(QThread):
    image_processed = pyqtSignal(QImage)
    points_detected = pyqtSignal(list)

    def __init__(self, parent: QObject) -> None:
        super().__init__(parent)
        self.camera = None
        self.stop = False

    def run(self) -> None:
        print("Camera started")
        self.camera = cv2.VideoCapture(0)
        self.camera.set(cv2.CAP_PROP_EXPOSURE, -9)
        while True:
            ret, frame = self.camera.read()
            ord_img = frame.copy()
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            bright_spots, img, thresh = find_points(img, ord_img)
            self.image_processed.emit(QImage(ord_img.data, ord_img.shape[1], ord_img.shape[0], ord_img.strides[0], QImage.Format_BGR888))
            self.points_detected.emit(bright_spots)
            while self.stop: pass
