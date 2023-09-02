import cv2
import itertools
import numpy as np
import mediapipe as mp
import matplotlib.pyplot as plt
import PIL
import os
import shutil


class Aligner(mp.solutions.face_mesh.FaceMesh):
  """Inherits from MediaPipe Face Mesh."""
  def __init__(
    self,
    static_image_mode: bool = True,
    max_num_faces: int = 1,
    refine_landmarks: bool = False,
    min_detection_confidence: float = 0.5,
    min_tracking_confidence: float = 0.5
  ):
    """Initializes a Image Aligner object.

    Unlike MediaPipe Face Mesh we set `static_image_mode` to `True` as we only
    require image manipulation.

    Args:
      static_image_mode: Whether to treat the input images as a batch of static
        and possibly unrelated images, or a video stream.
      max_num_faces: Maximum number of faces to detect.
      refine_landmarks: Whether to further refine the landmark coordinates
        around the eyes and lips, and output additional landmarks around the
        irises. Default to False.
      min_detection_confidence: Minimum confidence value ([0.0, 1.0]) for face
        detection to be considered successful.
      min_tracking_confidence: Minimum confidence value ([0.0, 1.0]) for the
        face landmarks to be considered tracked successfully.
    """
    super().__init__(
      static_image_mode=static_image_mode,
      max_num_faces=max_num_faces,
      refine_landmarks=refine_landmarks,
      min_detection_confidence=min_detection_confidence,
      min_tracking_confidence=min_tracking_confidence
    )

    self._left_eye_idx = list(
      set(itertools.chain(*mp.solutions.face_mesh.FACEMESH_LEFT_EYE))
    )[7]
    self._right_eye_idx = list(
      set(itertools.chain(*mp.solutions.face_mesh.FACEMESH_RIGHT_EYE))
    )[4]

  def _aligner(self, /, img: np.ndarray) -> np.ndarray:
    """Private helper function to align the given image parallel to the x-axis.

    This function creates a line between the left and right eye points and tries
    to align that line parallel to the x-axis, thus aligning the complete image.

    Args:
      img: Image to align parallel to the x-axis.
    """
    fm = self.process(img)
    if fm is None:
      return None

    points = []
    h, w, _ = img.shape

    face_landmarks = fm.multi_face_landmarks[0]

    le_x_coord = int(
      np.clip(face_landmarks.landmark[self._left_eye_idx].x * w, 0, w)
    )
    le_y_coord = int(
      np.clip(face_landmarks.landmark[self._left_eye_idx].y * h, 0, h)
    )
    p0 = np.array((le_x_coord, le_y_coord), dtype=np.float64)

    re_x_coord = int(
      np.clip(face_landmarks.landmark[self._right_eye_idx].x * w, 0, w)
    )
    re_y_coord = int(
      np.clip(face_landmarks.landmark[self._right_eye_idx].y * h, 0, h)
    )
    p1 = np.array((re_x_coord, re_y_coord), dtype=np.float64)

    h = abs(p0[1] - p1[1])
    w = abs(p0[0] - p1[0])

    # Get the angle between the x-axis and the line joining the eye points.
    theta = np.arctan(h / w)

    angle = (theta * 180) / np.pi

    if p0[0] < p1[0]:
      direction = 1 if p0[1] < p1[1] else -1
    else:
      direction = 1 if p1[1] < p0[1] else -1

    angle *= direction

    img = PIL.Image.fromarray(img)
    return np.array(img.rotate(angle))

  def align(self, /, imgs: tuple[np.ndarray]) -> list[np.ndarray]:
    """Aligns the given set of images parallel to the x-axis on the image plane.

    Args:
      imgs: Images to align parallel to the x-axis on the image place.
    """
    return [self._aligner(img) for img in imgs]
