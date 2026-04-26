from PyQt5.QtGui import QFontDatabase
from PyQt5.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
db = QFontDatabase()
families = db.families()
print("Available fonts:")
for f in sorted(families):
    if "Tajawal" in f:
        print(f"FOUND: {f}")
    if "Segoe" in f:
        print(f"Found: {f}")
