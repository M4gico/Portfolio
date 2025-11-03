import numpy as np

def treatment_black(array_picture: np.ndarray) -> np.ndarray:
    print("Make a treatment")
    return np.zeros(640*512).astype(np.uint16)

def AND_treatment(array_picture: np.ndarray) -> np.ndarray:
    print("AND TREATMENT")
    return np.array([0, 2, 3])