import numpy as np
from skimage.measure import block_reduce

# Purple threshholding method altered from Haseeb Nazki (hn33@st-andrews.ac.uk)

purple_threshold = 100    # Number of purple points for region to be considered purple
purple_scale_size = 16    # Scalar to use for reducing image to check for purple
def is_purple(crop: np.ndarray, purple_threshold: int,
              purple_scale_size: int) -> bool:
    """
    Determines if a given portion of an image is purple.
    Args:
        crop: Portion of the image to check for being purple.
        purple_threshold: Number of purple points for region to be considered purple.
        purple_scale_size: Scalar to use for reducing image to check for purple.
    Returns:
        A boolean representing whether the image is purple or not.
    """
    block_size = (crop.shape[0] // purple_scale_size,
                  crop.shape[1] // purple_scale_size, 1)
    pooled = block_reduce(image=crop, block_size=block_size, func=np.average)

    # Calculate boolean arrays for determining if portion is purple.
    r, g, b = pooled[..., 0], pooled[..., 1], pooled[..., 2]
    cond1 = r > g - 10
    cond2 = b > g - 10
    cond3 = ((r + b) / 2) > g + 20

    # Find the indexes of pooled satisfying all 3 conditions.
    pooled = pooled[cond1 & cond2 & cond3]
    num_purple = pooled.shape[0]

    return num_purple > purple_threshold

def is_valid_patch(patch):
  if is_purple(patch, purple_threshold, purple_scale_size) and patch.max() - patch.min() > 0:
    return True
