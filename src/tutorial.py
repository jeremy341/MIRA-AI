import cv2
import random

img =  cv2.imread('../data/Image.jpg', -1)  # Load an image from file


tag = img[500:700, 600:900] # copy from row 500 to row 700 and inside the columns 600 to 900, copying a square basically

img[100:300, 650:950] = tag # it needs to be same shape as what i copied so has to have the same dimensions as the copy

cv2.imshow('Image', img)
cv2.waitKey(0)
cv2.destroyAllWindows()

