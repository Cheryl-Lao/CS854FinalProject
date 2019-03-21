import cv2
import statistics
import time
import numpy as np

image_path = "../data/chessboard_large.jpg"
binary_path = "../data/binary.png"

# NOTE: OpenCV by RGB into Gray using a weighted average. BoofCV uses just the average
img = cv2.imread(image_path,cv2.IMREAD_GRAYSCALE)

# Binary image. 0 and 255. This matches what OpenCV expects
img_binary = cv2.imread(binary_path, cv2.IMREAD_GRAYSCALE)

region_radius = 5
region_width = region_radius*2+1

# Leave comment out for official benchmarks
# cv2.setNumThreads(0)

def gaussianBlur():
    cv2.GaussianBlur(img, (region_width, region_width), 0)

def gradientSobel():
    # Example converted it to CV_64F, which caused a massive slow down. Keeping it integer
    cv2.Sobel(img, cv2.CV_16S, 1, 0, ksize=1)
    cv2.Sobel(img, cv2.CV_16S, 0, 1, ksize=1)

def meanThresh():
    cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, region_width, 0)

def computeHistogram():
    hist =cv2.calcHist([img],[0],None,[256],[0,256])
    # for i in range(len(hist)):
    #     print("[{:3d}] {}".format(i,hist[i]))
    # print()
    # print("total = {}".format(sum(hist)))

def goodFeatures():
    # Documentation was ambiguous if this was a weighted or unweighted variant. This ambiguity was resolved
    # by running it on a chessboard image and seeing where the corners were found. it found them inside the square
    # and not on the corner, therefor it was the unweighted variant. I also inspected the C++ source code
    # and couldn't found any indication that Gaussian blur was applied
    kp=cv2.goodFeaturesToTrack(img,0,qualityLevel=0.016,minDistance=10,blockSize=21)
    # print("Shi-Tomasi count {}".format(len(kp)))

def computeCanny():
    # OpenCV's canny edge creates a binary image. This isn't very useful by itself. To process the edges you need
    # to extract the contours from the output binary image. I've used the values specified in an opencv example
    # https://docs.opencv.org/3.4.3/df/d0d/tutorial_find_contours.html
    edges = cv2.Canny(img, 15, 110)
    # print("total canny {}".format((np.asarray(edges) > 100).sum()))
    # Not approximating chains here since in the general purpose algorithms I've done a chain approximation would
    # require additional work.
    contours, hierarchy = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    # total = sum( len(c) for c in contours )
    # print("total canny contour {}".format(total))

# SIFT and SURF are not included in the standard distribution of Python OpenCV due to legal concerns
# Doing a custom build of OpenCV is beyond the scope scope of this benchmark since its only supposed to
# include what's easily available
if hasattr(cv2, 'xfeatures2d'):
    # This is configured to be similar to the SIFT paper with 5 octaves.
    # Target of 10,000 features to make comparison between libraries more accurate
    sift = cv2.xfeatures2d.SIFT_create(nfeatures=10000, nOctaveLayers=5, contrastThreshold=0.04, edgeThreshold=10, sigma=1.6)
    def detectSift():
        kp,des = sift.detectAndCompute(img, None)
        # print("SIFT found {:d}".format(len(kp)))

    # original paper had 4 scales per octave
    # threshold tuned to detect 10,000 features
    surf = cv2.xfeatures2d.SURF_create(hessianThreshold=420, nOctaves=4, nOctaveLayers=4, extended=False, upright=False)
    def detectSurf():
        kp,des = surf.detectAndCompute(img, None)
        # print("SURF found {:d}".format(len(kp)))

# TODO load an already thresholded image
# TODO contour
def contour():
    # Code in Validation Boof attempted to replicate the same behavior in both libraries. Configuration
    # values are taken from there.
    # The algorithm in OpenCV and the two contour algorithms in BoofCV operate internally very different
    # How OpenCV defines external and BoofCV define external is different
    contours, hierarchy = cv2.findContours(img_binary, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    # total = sum( len(c) for c in contours )
    # print("total pixels {}".format(total))

def houghLine():
    # OpenCV contains 3 Hough Line algorithms. CV_HOUGH_STANDARD is the closest to the variants included
    # in boofcv. The other OpenCV variants should have very different behavior based on their description

    lines = cv2.HoughLines(img, rho=5, theta=np.pi/180, threshold=15000)
    # print("total lines {}".format(len(lines)))

def benchmark( f , num_trials=10):
    times=[]
    for trials in range(num_trials):
        t0 = time.time()
        f()
        t1 = time.time()
        times.append(t1-t0)
    return statistics.mean(times)*1000

print("Gaussian Blur   {:.1f} ms".format(benchmark(gaussianBlur)))
print("meanThresh      {:.1f} ms".format(benchmark(meanThresh)))
print("gradient sobel  {:.1f} ms".format(benchmark(gradientSobel)))
print("histogram       {:.1f} ms".format(benchmark(computeHistogram,1)))
print("canny           {:.1f} ms".format(benchmark(computeCanny)))
if hasattr(cv2, 'xfeatures2d'):
    print("sift            {:.1f} ms".format(benchmark(detectSift, 10)))
    print("surf            {:.1f} ms".format(benchmark(detectSurf, 10)))
else:
    print("Skipping SIFT and SURF. Not installed")
print("contour         {:.1f} ms".format(benchmark(contour)))
print("good features   {:.1f} ms".format(benchmark(goodFeatures)))
print("hough polar     {:.1f} ms".format(benchmark(houghLine)))

print()
print("Done!")