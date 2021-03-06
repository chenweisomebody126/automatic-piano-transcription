import cv2
import imutils
import numpy as np
import itertools as it
from utils import *
from numpy.linalg import norm
from matplotlib import pyplot as plt

def degree(theta):
    return (180 * theta) / np.pi

def order_points(pts):
    # initialzie a list of coordinates that will be ordered
    # such that the first entry in the list is the top-left,
    # the second entry is the top-right, the third is the
    # bottom-right, and the fourth is the bottom-left
    rect = np.zeros((4, 2), dtype = "float32")

    sorted_y_indices = np.argsort(pts[:,1])
    rect[0], rect[1] = np.sort(pts[sorted_y_indices[:2],:], axis=0)
    rect[3], rect[2] = np.sort(pts[sorted_y_indices[2:],:], axis=0)

    # return the ordered coordinates
    return rect

def four_point_transform(image, pts):
    # obtain a consistent order of the points and unpack them
    # individually
    rect = order_points(pts)
    (tl, tr, br, bl) = rect
 
    # compute the width of the new image, which will be the
    # maximum distance between bottom-right and bottom-left
    # x-coordiates or the top-right and top-left x-coordinates
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))
 
    # compute the height of the new image, which will be the
    # maximum distance between the top-right and bottom-right
    # y-coordinates or the top-left and bottom-left y-coordinates
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))
 
    # now that we have the dimensions of the new image, construct
    # the set of destination points to obtain a "birds eye view",
    # (i.e. top-down view) of the image, again specifying points
    # in the top-left, top-right, bottom-right, and bottom-left
    # order
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype = "float32")
 
    # compute the perspective transform matrix and then apply it
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
 
    # return the warped image
    return warped

def getPerspectiveTransform(image, pts):
    rect = order_points(pts)
    (tl,tr,br,bl) = rect

    if norm(tl-tr) < 20 or norm(br-bl) < 20 or norm(tl-bl) < 20 or norm(tr-br) < 20:
        return None

    width_top = norm(tl-tr)
    width_bottom = norm(bl-br)
    width = max(int(width_top), int(width_bottom))

    height_left = norm(tl-bl)
    height_right = norm(tr-br)
    height = max(int(height_right), int(height_left))

    destination = np.array([[0,0], [width-1,0], [width-1, height-1],[0,height-1]], dtype = np.float32)

    M = cv2.getPerspectiveTransform(rect, destination)
    warped = cv2.warpPerspective(image, M, (width,height))

    return warped


def check_if_candidate_keyboard(image, maxBlackKeys=0):
    '''
    Checks if the given image is a candidate for a keyboard
    Returns:
        Number of black keys found in the top two third of the image
    '''
    H, W, _ = image.shape
    if H < 10:
        return

    H2_3 = int(2./3 * H)
    top_third = image[0:H2_3, :]
    lower_third = image[H2_3:,:]

    top_third_gray = cv2.cvtColor(top_third, cv2.COLOR_BGR2GRAY)
    lower_third_gray = cv2.cvtColor(lower_third, cv2.COLOR_BGR2GRAY)

    blur = cv2.GaussianBlur(top_third_gray,(5,5),0)
    _,top_thresh = cv2.threshold(top_third_gray,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    blur = cv2.GaussianBlur(lower_third_gray,(5,5),0)
    _,lower_thresh = cv2.threshold(lower_third_gray,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)

  
    if np.mean(top_thresh) < np.mean(lower_thresh):
        return detect_black_keys(top_third)
    return -1

def detectKeyboard(img):
    resized = cv2.resize(img, (240,320), cv2.INTER_AREA)
    ratio = img.shape[1] / float(resized.shape[1])

    edges = cv2.Canny(resized, 480, 500, 5)

    lines = cv2.HoughLines(edges, 1, np.pi/180, 50)
    lines = [l for l in lines if degree(l[0][1]) > 3  and degree(l[0][1]) <15]

    # ------------- x
    # |
    # |
    # |
    # |
    # |
    # y

    pairs = list(it.combinations(lines,2))

    for line1,line2 in pairs:
        pts = []
        for rho,theta in line1:
            a = np.cos(theta)
            b = np.sin(theta)

            x0 = rho * a
            y0 = rho * b
            x1 = int(x0 - 1000*b)
            y1 = int(y0 + 1000*a)
            x2 = int(x0 + 1000*b)
            y2 = int(y0 - 1000*a)

            m = (y2-y1) / (x2-x1)
            b = y0 - (m * x0)
            y = 0
            x = int((y-b)/m)
            pts.append([x,y])

            y = resized.shape[0]
            x = int((y-b)/m)
            pts.append([x,y])

        for rho,theta in line2:
            a = np.cos(theta)
            b = np.sin(theta)

            x0 = rho * a
            y0 = rho * b
            x1 = int(x0 - 1000*b)
            y1 = int(y0 + 1000*a)
            x2 = int(x0 + 1000*b)
            y2 = int(y0 - 1000*a)

            m = (y2-y1) / (x2-x1)
            b = y0 - (m * x0)
            y = 0
            x = int((y-b)/m)
            pts.append([x,y])

            y = resized.shape[0]
            x = int((y-b)/m)
            pts.append([x,y])
        pts = np.array(pts, dtype=np.float32)
        warped = getPerspectiveTransform(resized, pts)
        cv2.imshow('warped', warped)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

	return



def processedFrame(image):
    image = cv2.resize(image, (0,0), fx=0.5, fy=0.5)

    ymax, xmax, _ = image.shape
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5,5), 4)
    edged = auto_canny(blurred)

    i = 2
    while True:
        houghLines = cv2.HoughLines(edged, 1, np.pi/180*i, 100)
        if len(houghLines) < 30 or i>10:
            break
        i += 1
    lines = []

    for line in houghLines:
        for rho,theta in line:
                            
            if (theta >= 0.0 and theta < np.pi/180*30):
                continue
            a = np.cos(theta)
            b = np.sin(theta)
            x0 = a*rho
            y0 = b*rho
            x1 = int(x0 + 1000*(-b))
            y1 = int(y0 + 1000*(a))
            x2 = int(x0 - 1000*(-b))
            y2 = int(y0 - 1000*(a))


            if abs(90 - 180/np.pi*theta) > 5:
                x1 = int(get_x(rho, theta, 0))
                y1 = 0

                x2 = int(get_x(rho, theta, ymax-1))
                y2 = ymax-1
            else:
                x1 = 0
                y1 = int(get_y(rho, theta, x1))

                x2 = xmax
                y2 = int(get_y(rho, theta, x2))

            # cv2.line(image,(x1,y1),(x2,y2),(0,0,255),2)
            # display_image(image)
            l = Line(Point(x1,y1), Point(x2,y2), rho)
            lines.append(l)
    # display_image(image)

    pairs = list(it.combinations(lines,2))

    maxBlackKeys = 0
    candidate_keyboards = []
    for l1, l2 in pairs:
        warped = getPerspectiveTransform(image, np.array([(l1.start.x, l1.start.y), (l1.end.x, l1.end.y), (l2.start.x, l2.start.y), (l2.end.x, l2.end.y)]))
        if warped is not None:
            # display_image(warped)
            num_black_keys = check_if_candidate_keyboard(warped, maxBlackKeys)
            if num_black_keys >= maxBlackKeys:
                candidate_keyboards.append(warped)
                maxBlackKeys = num_black_keys

    for im in candidate_keyboards:
        detect_black_keys(im, True)
        # display_image(im)
    return edged

def display_image(image):
    cv2.imshow('', image)
    cv2.waitKey(0)
    return


def readVideo(filename):
    cap = cv2.VideoCapture(filename)

    flag = True
    while(cap.isOpened()):
        ret, frame = cap.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if flag:
            cv2.imwrite('frame-3.jpg', frame)
            flag = False

        # cv2.imshow('frame', processedFrame(frame))
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break 

    cap.release()
    cv2.destroyAllWindows()
    return

def get_first_frame(videoFilepath, frameFilepath):
    cap = cv2.VideoCapture(videoFilepath)

    flag = True
    while(cap.isOpened()):
        ret, frame = cap.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if flag:
            cv2.imwrite(frameFilepath, frame)
            flag = False
            break
    cap.release()
    cv2.destroyAllWindows()
    return

def main():
    # img = cv2.imread('data/arjun1.jpg')
    # img = cv2.imread('keyboard-2.jpg')
    img = cv2.imread('testimage2.jpg')
    # detectKeyboard(img)	
    # readVideo('vid-3.mp4')
    # img = cv2.imread('frame-3.jpg')
    # img = cv2.imread('img.png')
    
    # img = cv2.imread('img.png')    
    # detect_black_keys(img)
    
    img = cv2.imread('frame-jazz-tut-1.jpg')    
    # img = cv2.imread('frame-3.jpg')    
    processedFrame(img)

    # get_first_frame('vid\\sample-jazz-tut-1.mp4', 'frame-jazz-tut-1.jpg')

    return

if __name__ == '__main__':
	main()