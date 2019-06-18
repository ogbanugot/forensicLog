# forensicLog
Webcam facial recognition and event log with python (Windows only). When run, a display of the facial recognition on the video feed is displayed with a bounding box and identified persons name. Event logs of the users actions are also saved. 
  
## Install requirements 
pip install -r requirements.txt  

## Usage 
run the command  
python recognize_faces_video_module.py

in another terminal  
python eventlog.py

## Logs  
Check the directory for the event logs and ./output for the video log

## Train your own dataset  
python encode_faces.py --dataset <path/to/dataset> --encodings encodings.pickle  
directory structure should be;  
/dataset/class e.g /dataset/ogban_ugot


