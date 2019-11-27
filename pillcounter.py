#Made by Steven Lewis
import cv2
import numpy as np
import bisect
import math
from flask import Flask, request, redirect, send_from_directory
from scipy._lib.six import xrange
from werkzeug.utils import secure_filename

debug = False
UPLOAD_FOLDER = '/Users/jeunetoujour/uploads'
ALLOWED_EXTENSIONS = set(['jpg', 'jpeg'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])


def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            #flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            #flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            image = np.asarray(bytearray(file.read()), dtype="uint8")
            img2 = cv2.imdecode(image, cv2.IMREAD_COLOR)
            img = cv2.imdecode(image, cv2.IMREAD_GRAYSCALE)

            #make deep copy of original
            orig = np.zeros(img2.shape)
            np.copyto(orig, img2)

            rows, cols = img.shape[:2]
            #blur image to soften edges
            #img = cv2.GaussianBlur(img, (5, 5), 0)
            img = cv2.bilateralFilter(img, 10, 20, 5)
            if(debug == True):
                cv2.imwrite(app.config['UPLOAD_FOLDER'] + "/bi_" + filename, img)

            #Good luck understanding what this is doing, muhahaha
            kernel_x = cv2.getGaussianKernel(int(cols), cols * 0.90)
            kernel_y = cv2.getGaussianKernel(int(rows), rows * 0.90)
            kernel = kernel_y * kernel_x.T
            mask = 2500 * kernel / np.linalg.norm(kernel)

            # applying the mask to main channel in the input image
            img[:, :] = img[:, :] * mask

            #save original image
            cv2.imwrite(app.config['UPLOAD_FOLDER'] + "/orig_" + filename, img2)

            #apply histograms dynamic threshold value and make binary image
            thresh, img = cv2.threshold(img, 0, 256, cv2.THRESH_OTSU + cv2.THRESH_BINARY_INV)
            #print "First thresh " + str(thresh)

            if(debug == True):
                cv2.imwrite(app.config['UPLOAD_FOLDER'] + "/thresh1_" + filename, img)

            image1 = img

            #this is the same as fillconvexpoly by finding holes and filling, still same issue, needs RETR_CCOMP
            # for i in xrange(0, len(contours)):
            #     #print hierarchy[0][i][3]
            #     if hierarchy[0][i][3] != -1:
            #         #print "I'm inside" + str(i)
            #         cv2.drawContours(image1, contours, i, (255,255,255), -1)

            _, contours, hierarchy = cv2.findContours(
                image1,
                cv2.RETR_TREE,
                cv2.CHAIN_APPROX_SIMPLE
            )

            con = 0

            #find all the pills you can and apply white mask of contours over it to clean insides (advil use case)
            for cnt in contours:
                area = cv2.contourArea(cnt)
                perim = cv2.arcLength(cnt, True) + .0000001
                ratio =  area / perim
                #print ratio
                if ratio < 5:
                    #finds small white blobs and makes them black, better close

                    #print "Area: " + str(area)
                    cv2.drawContours(image1, contours, con, (0, 0, 0), -1)

                #cv2.fillConvexPoly(image1, cnt, (255, 255, 255))
                #cv2.drawContours(image1, contours, con, (255, 255, 255), -1)
                con += 1

            #invert back
            image1 = cv2.bitwise_not(image1)

            if(debug == True):
                cv2.imwrite(app.config['UPLOAD_FOLDER'] + "/thresh11_" + filename, image1)

            _, contours, hierarchy = cv2.findContours(
                image1,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )

            con = 0

            # cleans white spots on outside of contours
            for cnt in contours:
                area = cv2.contourArea(cnt)

                if area < 1500:
                    # finds small white blobs and makes them black, better close
                    cv2.drawContours(image1, contours, con, (0, 0, 0), -1)

                con += 1

            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            image1 = cv2.erode(image1, kernel, iterations=7)

            if(debug == True):
                cv2.imwrite(app.config['UPLOAD_FOLDER'] + "/thresh0_" + filename, image1)

            #This creates a matrix to "Sand" the edges of the pills to break them apart better
            #kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            #image1 = cv2.morphologyEx(image1, cv2.MORPH_OPEN, kernel, iterations=1)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
            image1 = cv2.erode(image1, kernel, iterations=9)


            if(debug == True):
                cv2.imwrite(app.config['UPLOAD_FOLDER'] + "/thresh2_" + filename, image1)

            _, contours, hierarchy = cv2.findContours(
                image1,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )

            # #go through contours to find defects where they are connected, try to punch hole connected pills
            # for cnt in contours:
            #     hull = cv2.convexHull(cnt, returnPoints=False)
            #     defects = cv2.convexityDefects(cnt, hull)
            #     if defects is not None:
            #         for i in range(defects.shape[0]):
            #             s, e, f, d = defects[i, 0]
            #             far = tuple(cnt[f][0])
            #             #if d > 10000:
            #                #cv2.circle(image1, far, 26, (0, 0, 0), -1)

            trueavg, sideratio = get_true_avg(contours)
            if trueavg >= 40000:
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9,9))
                tophat = cv2.morphologyEx(image1, cv2.MORPH_OPEN, kernel, iterations=3)
                image1 = tophat
                #cv2.imwrite(app.config['UPLOAD_FOLDER'] + "/tophat_" + filename, tophat)
            if trueavg > 20000 and trueavg < 40000:
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
                tophat = cv2.morphologyEx(image1, cv2.MORPH_OPEN, kernel, iterations=3)
                image1 = tophat
                #cv2.imwrite(app.config['UPLOAD_FOLDER'] + "/tophat_" + filename, tophat)
            if trueavg <= 20000:
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
                tophat = cv2.morphologyEx(image1, cv2.MORPH_OPEN, kernel, iterations=3)
                image1 = tophat
                #cv2.imwrite(app.config['UPLOAD_FOLDER'] + "/tophat_" + filename, tophat)

            defectFound = True
            j = 0 
            while defectFound == True:
              j = j + 1
              _, contours, hierarchy = cv2.findContours(
                image1,
                #cv2.RETR_EXTERNAL,
                cv2.RETR_CCOMP,
                cv2.CHAIN_APPROX_NONE
              )
              defectFound = False
              erode_threshold = 3.25
              for i in xrange(0, len(contours)):
              #for contour in contours:

                contour = contours[i]
                hier = hierarchy[0][i]

                #If the contour is large, try eroding just that contour
                if cv2.contourArea(contour) > erode_threshold * trueavg and hier[3] == -1:
                    defectFound = True
                    #create new image
                    #fill new image with black
                    mask = np.zeros_like(image1)
                    #draw contour on old image with black
                    cv2.drawContours(image1, [contour], 0, 0, -1)
                    #draw contour on new image
                    cv2.drawContours(mask, [contour], 0, 255, -1)
                    while hier[2] != -1 or (hier[2] == -1 and hier[0] != -1):
                        if hier[2] != -1:
                            index = hier[2]
                        else :
                            index = hier[0]
                        subcontour = contours[index]
                        hier = hierarchy[0][index]
                        cv2.drawContours(mask, [subcontour], 0, 0, -1)

                    hier = hierarchy[0][i]
                    if(debug == True):
                        cv2.imwrite(app.config['UPLOAD_FOLDER'] + "/single_contour_" + str(j) + "_" + str(cv2.contourArea(contour)) + ".jpg", mask)
                    #erode new image
                    #kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
                    #mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

                    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
                    mask = cv2.erode(mask, kernel, iterations=5)
                    #kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
                    #mask = cv2.dilate(mask, kernel, iterations=1)
                    if(debug == True):
                        cv2.imwrite(app.config['UPLOAD_FOLDER'] + "/single_contour2_" + str(j) + "_" + str(cv2.contourArea(contour)) + ".jpg", mask)
                    #find contours on new image
                    _, new_contours, new_hierarchy = cv2.findContours(
                        mask,
                        cv2.RETR_EXTERNAL,
                        cv2.CHAIN_APPROX_SIMPLE
                    )

                    if (len(new_contours) > 1):
                        #print "Dilating"
                        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
                        mask = cv2.dilate(mask, kernel, iterations=2)
                    #find contours on new image
                    _, new_contours, new_hierarchy = cv2.findContours(
                        mask,
                        cv2.RETR_CCOMP,
                        cv2.CHAIN_APPROX_SIMPLE
                    )
                    #draw contours on old image with white
                    for j in xrange(0, len(new_contours)):
                        cnt = new_contours[j]
                        hier = new_hierarchy[0][j]
                        if hier[3] == -1:
                            cv2.drawContours(image1, [cnt], -1, 255, -1)
                        else:
                            cv2.drawContours(image1, [cnt], -1, 0, -1)
                    if(debug == True):
                        cv2.imwrite(app.config['UPLOAD_FOLDER'] + "/rebuilt_" + str(j) + ".jpg", image1)

 
                # If the contour is the roughly the same size as all the others, don't perform convexity analysis
                #
                if cv2.contourArea(contour) > 1.1 * trueavg and cv2.contourArea(contour) <= erode_threshold * trueavg and hier[3] == -1:
                    #print "Performing convex analysis."
                    #print "j = " + str(j)
                    hull = cv2.convexHull(contour, returnPoints=False)
                    defects = cv2.convexityDefects(contour, hull)
                    if defects is None:
                        defects = []
                    polyPoints = []
                    if len(defects) != 0:
                        total_d = 0
                        valid_defects = 0
                        avg_d = 0
                        # This average defect distance is to try to eliminate some noise introduced by iterative slicing, I haven't seen it fail, but if there is one very large defect as writen 
                        # this may have problems as it is writen.  Using the median eliminates too many defects though.
                        for i in range(defects.shape[0]):
                            s, e, f, d = defects[i, 0]
                            if d > 5000:
                               total_d = total_d + d
                               valid_defects = valid_defects + 1
                        if valid_defects < 4:
                            avg_d = 4000
                        else:
                            avg_d = total_d / valid_defects
                        for i in range(defects.shape[0]):
                            s, e, f, d = defects[i, 0]
                            far = tuple(contour[f][0])
                            ############  As opposed to having d's limit hard coded at 2000, compute it dynamically based upon the area and the length,
                            ############  I don't remember exacly why it was multiplied by 256 but it was due to somthing odd about arcLength if I recall correctly
                            if d > avg_d or d > 10000:
                            #if d > (cv2.contourArea(contour) / (0.001*cv2.arcLength(contour, True)) - 1) * 256:
                                polyPoints.append([far, s, e])
                    minDistance = 1000000000000
                    startPoint = None
                    endPoint = None
                    for point in polyPoints:
                         for point2 in polyPoints:
                            distance = ((point[0][0] - point2[0][0])**2 + (point[0][1] - point2[0][1])**2) ** 0.5
                            convex_hull_proximity = min(math.fabs(point[2] - point2[1]), len(contour) - math.fabs(point[2] - point2[1]))/len(contour)
                            convex_hull_proximity2 = min(math.fabs(point2[2] - point[1]), len(contour) - math.fabs(point2[2] - point[1]))/len(contour)
                            convex_hull_proximity = min(convex_hull_proximity, convex_hull_proximity2)
                            #print "Points " + str(point[1]) + " " + str(point[2]) + " " + str(point2[1]) + " " + str(point2[2]) + " " + str(len(contour))
                           # #print convex_hull_proximity
                            multiplier = ((-1/((convex_hull_proximity +1 )**2)) +1)
                            #print multiplier
                            if(multiplier == 0):
                                multiplier = .0000001
                            distance = distance / multiplier
                            #print distance
                            if distance != 0 and distance < minDistance:
                                  minDistance = distance
                                  startPoint = point[0]
                                  endPoint = point2[0]
                    #polyArray = np.array(polyPoints, np.int32)
                    #if len(polyPoints) > 2:
                    #    cv2.fillPoly(image1, [polyArray], (0, 0, 0), 4)
                    if len(polyPoints) >= 2:
                        cv2.line(image1, startPoint, endPoint, (0, 0, 0), 44)
                        defectFound = True
                    #print "Completed loop"
                    if(debug == True):
                        cv2.imwrite(app.config['UPLOAD_FOLDER'] + "/slice_" + str(j) + ".jpg", image1)

            if(debug == True):
                cv2.imwrite(app.config['UPLOAD_FOLDER'] + "/thresh3_" + filename, image1)

            _, contours, hierarchy = cv2.findContours(
                image1,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )

            j = 0



            #print "TrueAvg: " + str(trueavg)

            testavg = 0
            for cnt in contours:
                area = cv2.contourArea(cnt)
                testavg += area

                #print area
                #if contour is too small or large to be a pill, ignore
                if area < 1800:
                    continue
                if area > 3500000:
                    #print "Too large2"
                    continue

                #calculate contour vs median area to see if its multiple pills or not
                density = ((cv2.contourArea(cnt) / trueavg) - 1)
                #print "Density: " + str(density)
                #if its X.70 it will round up for another pill increment count
                if density > 0.70:
                    #print "Div: " + str(density)
                    maindec = str(density-int(density))[2:3]
                    #j += int(density)
                    if float(maindec) > 7.0:
                        j += 0

            for contour in contours:
                area = cv2.contourArea(contour)

                if area < 1800:
                    continue

                if area > 17000000:
                    continue

                #add to the count as its a normal pill
                j += 1

                #building the box to display on image of where contour is
                rect = cv2.minAreaRect(contour)
                box = cv2.boxPoints(rect)
                box = np.int0(box)
                cv2.drawContours(orig, [box], 0, (0, 205, 0), 18)

            #end of program, write count on Image, and save final image with AR info
            cv2.putText(orig, "Count: " + str(j), (40, 280), cv2.FONT_HERSHEY_SIMPLEX, 11, (255, 255, 255), 11)
            if sideratio > 1.5:
                cv2.putText(orig, "Oblong", (40, 580), cv2.FONT_HERSHEY_SIMPLEX, 11, (255, 255, 255), 11)
            else:
                cv2.putText(orig, "Circular", (40, 580), cv2.FONT_HERSHEY_SIMPLEX, 11, (255, 255, 255), 11)
            #cv2.putText(orig, "GuessCount: " + str(testavg / trueavg), (40, 580), cv2.FONT_HERSHEY_SIMPLEX, 6, (255, 255, 255), 11)

            r = 720.0 / orig.shape[1]
            dim = (720, int(orig.shape[0] * r))
            resized = cv2.resize(orig, dim, interpolation=cv2.INTER_AREA)

            cv2.imwrite(app.config['UPLOAD_FOLDER'] + "/" + filename, resized, [int(cv2.IMWRITE_JPEG_QUALITY), 40])

            #print testavg/trueavg
            #for now, make string of count and return that as body to POST call
            scount = "Count:" + str(j)
            print scount
            return scount   #redirect(url_for('uploaded_file', filename=filename, headers=headers))
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def get_true_avg(contours):
    areaarray = []
    sideratio = 0.00001
    for cnt in contours:
        bisect.insort(areaarray, cv2.contourArea(cnt))

    # get the median area of a pill to use as an avg size
    # Examples have come up where the median pill is still in the multipill size range, dropping the index down by 2
    index = int(len(areaarray)) / 2
    if (index > 6):
        index = index - 2
    trueavg = areaarray[index]
    # print "Old trueavg = " + str(trueavg)
    sorted_contours = sorted(contours, key=cv2.contourArea)
    sorted_contours.reverse()
    for contour in sorted_contours:
        hull = cv2.convexHull(contour, returnPoints=False)
        defects = cv2.convexityDefects(contour, hull)
        defectFound = False
        if defects is None:
            defects = []
        for i in range(defects.shape[0]):
            s, e, f, d = defects[i, 0]
            if (d > 5000):
                defectFound = True
        if (defectFound == False):
            # print "Defect free contour found"
            trueavg = cv2.contourArea(contour)
            rect = cv2.minAreaRect(contour)
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            print "Side a: "
            sidea = ((box[0][0] - box[1][0])**2 + (box[0][1] - box[1][1])**2) **0.5
            print sidea
            print "Side b: "
            sideb = ((box[1][0] - box[2][0])**2 + (box[1][1] - box[2][1])**2) **0.5
            print sideb
            sideratio = sidea/sideb
            if sideratio < 1:
                sideratio = 1/sideratio
            print "Ratio: " + str(sideratio)
            print box
            break

    print "New trueavg = " + str(trueavg)
    return trueavg, sideratio

if __name__ == '__main__':
    app.run()
    #app.run(host='127.0.0.1', port=5000)
