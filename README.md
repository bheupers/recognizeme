# RecognizeME

For a while I have been looking at automatic face recognition. This is becoming more and more mainstream. When I enter the border of my home country my face is 
checked against something in my passport, and phones can be unlocked by faces. But it is interesting to know how this works and it would be nice to have some 
program to test and play with face recognition.

For this purpose I build RecognizeME. This is a website where recognize faces that were added earlier. Images for these faces can be made by uploading files or 
by the camera of your computer or smartphone.

For the face recognition itself I used the DLIB C++ library together with the face_recognition Python library. This does all the hard work. It uses a pre-trained 
model for face recognition that will first find faces in an image. Then for the faces found it will compute an encoding . This encoding can be compared with 
another encoding for other images, and these encodings are similar we can say these faces are identical. DLIB claims an impressive accuracy of 99.38% on the 
standard Labeled Faces in the Wild dataset. In my RecognizeME website it does seem to work quite well for the few people I used for testing.

The RecognizeME website is a Python aiohttp application. In this aiohttp setup the time consuming recognition requests are being dispatched to another process
 in pool of workers. And non-recognition requests are not blocked by these time-consuming requests.

For running these kind of deep-learning applications it is faster to use some kind of GPU acceleration. The DLIB library can be compiled with CUDA support. 
I wanted to try this on my recently acquired Jetson Nano Developer Kit. This is a device similar to a Raspberry PI, but with a much faster GPU and does not 
draw much power. It runs Ubuntu and Nginx, and is now part of my home datacenter that serves my website https://bartheupers.nl/recognizeme/

When I compare the recognition performance on this Jetson Nano to my MacBook Pro with a Intel Core i7, but no CUDA GPU, then the Jetson Nano does a recognition in 
approx 1 second, while the MacBook takes three seconds for this task. So I am happy to be able to use the Jetson Nano for this and have both an acceptable performance 
and electricity bill for my home data center.

The CUDA on my Jetson Nano had one disadvantage in that is supported only one worker process at the same time. When enabling multiple workers I got a CUDA error 3, 
related to multiprocessing. But for now I am can live with only one worker.

For the image handling some Javascript was required to deal with the HTML5 canvas and the camera.

# Instruction

To install this we first need to install DLIB. Follow instructions for installing this on for example https://www.pyimagesearch.com/2017/03/27/how-to-install-dlib/
  
Then do :

```
git clone https://github.com/bheupers/recognizeme.git
cd recognizeme
virtualenv --python=python3 --prompt='RM>' venv
source venv/bin/activate
pip install -r requirements.txt
```

Finally we can run the program  with :

python -m facerecognition


and test on : http://localhost:8000/recognizeme/

# Autostart

Use systemd :

```
/etc/systemd/system/recognizeme.service
```

```
[Unit]
Description=Recognizeme service

[Service]
User=bart
WorkingDirectory=/home/bart/sites/recognizeme
ExecStart=/home/bart/sites/recognizeme/start.sh
StandardOutput=file:/var/log/recognizeme.log
StandardError=file:/var/log/recognizeme.err
Restart=always

[Install]
WantedBy=multi-user.target
```

```
sudo systemctl start|stop|status|restart recognizeme
```