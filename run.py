# import the necessary packages
from imutils.video import VideoStream
import face_recognition
import argparse
import imutils
import pickle
import time
import cv2

import codecs
import os
import sys
import time
import traceback
import win32con
import win32evtlog
import win32evtlogutil
import winerror
from twisted.internet import task, reactor


global currentUsers
# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-y", "--display", type=int, default=1,
	help="whether or not to display output frame to screen")
ap.add_argument("-d", "--detection-method", type=str, default="hog",
	help="face detection model to use: either `hog` or `cnn`")
args = vars(ap.parse_args())

# load the known faces and embeddings
print("[INFO] loading encodings...")
data = pickle.loads(open("encodings.pickle", "rb").read())

# initialize the video stream and pointer to output video file, then
# allow the camera sensor to warm up
print("[INFO] starting video stream...")
vs = VideoStream(src=0).start()
time.sleep(2.0)

def facialRec():
    writer = None
    # loop over frames from the video file stream
    while True:
        # grab the frame from the threaded video stream
        frame = vs.read()
        
        # convert the input frame from BGR to RGB then resize it to have
        # a width of 750px (to speedup processing)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb = imutils.resize(frame, width=750)
        r = frame.shape[1] / float(rgb.shape[1])

        # detect the (x, y)-coordinates of the bounding boxes
        # corresponding to each face in the input frame, then compute
        # the facial embeddings for each face
        boxes = face_recognition.face_locations(rgb,
            model=args["detection_method"])
        encodings = face_recognition.face_encodings(rgb, boxes)
        names = []

        # loop over the facial embeddings
        for encoding in encodings:
            # attempt to match each face in the input image to our known
            # encodings
            matches = face_recognition.compare_faces(data["encodings"],
                encoding)
            name = "Unknown"

            # check to see if we have found a match
            if True in matches:
                # find the indexes of all matched faces then initialize a
                # dictionary to count the total number of times each face
                # was matched
                matchedIdxs = [i for (i, b) in enumerate(matches) if b]
                counts = {}

                # loop over the matched indexes and maintain a count for
                # each recognized face face
                for i in matchedIdxs:
                    name = data["names"][i]
                    counts[name] = counts.get(name, 0) + 1

                # determine the recognized face with the largest number
                # of votes (note: in the event of an unlikely tie Python
                # will select first entry in the dictionary)
                name = max(counts, key=counts.get)
            
            # update the list of names
            names.append(name)
            currentUsers = names

        # loop over the recognized faces
        for ((top, right, bottom, left), name) in zip(boxes, names):
            # rescale the face coordinates
            top = int(top * r)
            right = int(right * r)
            bottom = int(bottom * r)
            left = int(left * r)

            # draw the predicted face name on the image
            cv2.rectangle(frame, (left, top), (right, bottom),
                (0, 255, 0), 2)
            y = top - 15 if top - 15 > 15 else top + 15
            cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX,
                0.75, (0, 255, 0), 2)

        # if the video writer is None *AND* we are supposed to write
        # the output video to disk initialize the writer
        if writer is None:
            fourcc = cv2.VideoWriter_fourcc(*"MJPG")
            writer = cv2.VideoWriter("output/webcam_face_recognition_output.avi", fourcc, 20,
                (frame.shape[1], frame.shape[0]), True)

        # if the writer is not None, write the frame with recognized
        # faces t odisk
        if writer is not None:
            writer.write(frame)

        # check to see if we are supposed to display the output frame to
        # the screen
        if args["display"] > 0:
            cv2.imshow("Frame", frame)
            key = cv2.waitKey(1) & 0xFF

            # if the `q` key was pressed, break from the loop
            if key == ord("q"):
                break

    # do a bit of cleanup
    cv2.destroyAllWindows()
    vs.stop()

    # check to see if the video writer point needs to be released
    if writer is not None:
        writer.release()

#----------------------------------------------------------------------
def getAllEvents(server, logtypes, basePath):
    """
    """
    if not server:
        serverName = "localhost"
    else: 
        serverName = server
    for logtype in logtypes:
        path = os.path.join(basePath, "%s_%s_log.txt" % (serverName, logtype))
        getEventLogs(server, logtype, path)
 
#----------------------------------------------------------------------
def getEventLogs(server, logtype, logPath):
    """
    Get the event logs from the specified machine according to the
    logtype (Example: Application) and save it to the appropriately
    named log file
    """
    print("Logging %s events" % logtype)
    log = codecs.open(logPath, encoding='utf-8', mode='w')
    line_break = '-' * 80
 
    log.write("\n%s Log of %s Events\n" % (server, logtype))
    log.write("Created: %s\n\n" % time.ctime())
    log.write("\n" + line_break + "\n")
    hand = win32evtlog.OpenEventLog(server,logtype)
    total = win32evtlog.GetNumberOfEventLogRecords(hand)
    print("Total events in %s = %s" % (logtype, total))
    flags = win32evtlog.EVENTLOG_BACKWARDS_READ|win32evtlog.EVENTLOG_SEQUENTIAL_READ
    events = win32evtlog.ReadEventLog(hand,flags,0)
    evt_dict={win32con.EVENTLOG_AUDIT_FAILURE:'EVENTLOG_AUDIT_FAILURE',
              win32con.EVENTLOG_AUDIT_SUCCESS:'EVENTLOG_AUDIT_SUCCESS',
              win32con.EVENTLOG_INFORMATION_TYPE:'EVENTLOG_INFORMATION_TYPE',
              win32con.EVENTLOG_WARNING_TYPE:'EVENTLOG_WARNING_TYPE',
              win32con.EVENTLOG_ERROR_TYPE:'EVENTLOG_ERROR_TYPE'}
 
    try:
        events=1
        while events:
            events=win32evtlog.ReadEventLog(hand,flags,0)
 
            for ev_obj in events:
                the_time = ev_obj.TimeGenerated.Format() #'12/23/99 15:54:09'
                evt_id = str(winerror.HRESULT_CODE(ev_obj.EventID))
                computer = str(ev_obj.ComputerName)
                cat = ev_obj.EventCategory
        ##        seconds=date2sec(the_time)
                record = ev_obj.RecordNumber
                msg = win32evtlogutil.SafeFormatMessage(ev_obj, logtype)
 
                source = str(ev_obj.SourceName)
                if not ev_obj.EventType in evt_dict.keys():
                    evt_type = "unknown"
                else:
                    evt_type = str(evt_dict[ev_obj.EventType])
                log.write("Event Date/Time: %s\n" % the_time)
                log.write("Event ID / Type: %s / %s\n" % (evt_id, evt_type))
                log.write("Currently Active User(s): %s\n" % currentUsers)
                log.write("Record #%s\n" % record)
                log.write("Source: %s\n\n" % source)
                log.write(msg)
                log.write("\n\n")
                log.write(line_break)
                log.write("\n\n")
    except:
        print (traceback.print_exc(sys.exc_info()))
 
    print ("Log creation finished. Location of log is %s" % logPath)
    
if __name__=="__main__":
    server = None  # None = local machine
    logTypes = ["System", "Application"]
    dir = os.path.dirname(os.path.realpath(__file__))
    getAllEvents(server, logTypes, dir)
    facialRec()
    #timeout = 60.0 # Sixty seconds
    #dir = os.path.dirname(os.path.realpath(__file__))
    #l = task.LoopingCall(getAllEvents(server, logTypes, dir))
    #l.start(timeout) # call every sixty seconds
    #reactor.run()
    #eventlog()