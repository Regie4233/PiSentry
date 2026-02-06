import sys
import pkg_resources

print(f"Python: {sys.executable}")
print("Installed packages matching 'picamera':")
for p in pkg_resources.working_set:
    if "picamera" in p.project_name.lower():
        print(f"  {p.project_name} ({p.version})")
        try:
            # Try to find top_level.txt to see what modules it provides
            dist = pkg_resources.get_distribution(p.project_name)
            if dist.has_metadata("top_level.txt"):
                print("    Modules:", list(dist.get_metadata_lines("top_level.txt")))
        except Exception as e:
            print(f"    Error reading metadata: {e}")

print("\nImport Attempts:")
try:
    import picam2

    print("SUCCESS: import picam2")
except ImportError as e:
    print(f"FAIL: import picam2 ({e})")

try:
    import picamera2

    print("SUCCESS: import picamera2")
except ImportError as e:
    print(f"FAIL: import picamera2 ({e})")
