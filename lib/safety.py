import py5
import numpy as np

_prev_frame = None

def apply_anti_flicker_filter(strength=0.5):
    """
    Applies a temporal blending filter to the current frame to reduce high-frequency flicker.
    This effectively creates a motion blur / trails effect.
    
    strength: float (0.0 to 1.0). 
              0.0 means no effect. 
              1.0 means infinite trails (screen never updates).
              0.5 is a balanced default for mitigating >3Hz flashing.
    """
    global _prev_frame
    
    # Load the current frame's pixels into py5.np_pixels
    py5.load_np_pixels()
    
    current = py5.np_pixels.copy()
    
    if _prev_frame is None:
        _prev_frame = current.copy()
        return
        
    # Blend current with previous (using float for precision, then back to uint8)
    blended = (current.astype(np.float32) * (1.0 - strength) + _prev_frame.astype(np.float32) * strength)
    blended_uint8 = blended.astype(np.uint8)
    
    # Update the global tracker
    _prev_frame = blended_uint8.copy()
    
    # Push the blended pixels back to the screen
    py5.np_pixels[:] = blended_uint8
    py5.update_np_pixels()
