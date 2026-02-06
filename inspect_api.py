from picamera2 import Picamera2
import inspect

print("Inspecting Picamera2 Class:")
try:
    print(f"Dir: {dir(Picamera2)}")

    # Try to verify if it's the libcamera one or something else
    picam = Picamera2()
    print(f"\nInstance Dir: {dir(picam)}")

    if hasattr(picam, "configure"):
        print("\nMethod 'configure' found.")
        print(inspect.signature(picam.configure))

    if hasattr(picam, "create_configuration"):
        print("\nMethod 'create_configuration' found.")
    else:
        print("\nMethod 'create_configuration' NOT found.")

    if hasattr(picam, "create_video_configuration"):  # Older name?
        print("\nMethod 'create_video_configuration' found.")

except Exception as e:
    print(f"\nError during inspection: {e}")
