# Team 17 Object Tracking Project using Yolov7 + StrongSORT with OSNet





<div align="center">
<p>
<img src="MOT16_eval/track_pedestrians.gif" width="400"/> <img src="MOT16_eval/track_all.gif" width="400"/> 
</p>
<br>  
</div>


## Introduction
This project is based on the [Yolov7_StrongSORT_OSNet] (https://github.com/mikel-brostrom/Yolov7_StrongSORT_OSNet) by author Mikel Broström.
The original work is licensed by GNU GENERAL PUBLIC LICENSE. Some modifications and adaptation have been made to suit the needs of this project.

## Before you run the app

1. Clone the repository recursively:

`git clone --recurse-submodules https://github.com/tprabaka/objectTrackingCCN.git`

If you already cloned and forgot to use `--recurse-submodules` you can run `git submodule update --init`

2. Make sure that you fulfill all the requirements: Python 3.11 or later with all [requirements.txt](https://github.com/tprabaka/objectTrackingCCN/blob/main/requirements.txt) dependencies installed, including torch>=1.7. To install, run:

`pip install -r requirements.txt`


## Running the Projecct
After installing all the packages from requirements. Run the [app.py](https://github.com/tprabaka/objectTrackingCCN/blob/main/app.py).

`python app.py`

Then in the command it will the show the link in which the projecct is running it should mostly be this website address. Cross check with the console to see the correct URL.

`http://0.0.0.0:8080`
