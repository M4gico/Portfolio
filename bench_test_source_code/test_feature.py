from PyQt6.QtGui import QPixmap, QImage, QIcon
import numpy as np

try:
    png = QIcon(r"C:\EMMI_Soft\BancEMMI\FolderToTest\ABI\PictureDraft\Picture_xy_1.png").pixmap()
except Exception as e:
    print(e)

image = png.toImage().convertToFormat(QImage.Format.Format_RGBX64)

#Get raw bytes from the image
ptr = image.constBits()
ptr.setsize(image.sizeInBytes())

arr = np.frombuffer(ptr, dtype=np.uint16).reshape(image.height(), image.width(), 4)

print(arr)