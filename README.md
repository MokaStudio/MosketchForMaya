![Mosketch for Maya](https://user-images.githubusercontent.com/7549728/28314038-58406cb0-6bb9-11e7-87bc-47d7f9e3d46d.png)

# [Mosketch&trade;](https://www.mokastudio.com) for Maya
```mosketch_for_maya.py``` is a simple Python script showcasing how to stream joints values (orientation and translation) from [Mosketch&trade;](https://www.mokastudio.com) to Maya (and vice versa). You need to start [streaming in Mosketch](http://support.mokastudio.com/support/solutions/articles/6000176455-streaming) first.

Feel free to adapt it and port it to any other software.

Please note that the main purpose is to keep the script as short and simple as possible.

## Installation
First, download and uncompress [MosketchForMaya-master.zip](https://github.com/MokaStudio/MosketchForMaya/archive/master.zip). Then copy all files into your local scripts folder:
* __Windows:__ ```<My Documents>\maya\scripts```
* __MacOSX:__ ```/Users/<username>/Library/Preferences/Autodesk/maya/scripts/```

Then, open Maya's [script editor](https://knowledge.autodesk.com/support/maya/learn-explore/caas/CloudHelp/cloudhelp/2017/ENU/Maya/files/GUID-7C861047-C7E0-4780-ACB5-752CD22AB02E-htm.html) and copy-paste the following script in a Python console tab:
```python
import mosketch_for_maya
mosketch_for_maya.install()
```
Then press ![Execute Script](https://user-images.githubusercontent.com/7549728/28462913-d907f49c-6e1d-11e7-9b70-6c71b69b41e8.png) (at the top of the Script Editor) to execute it.

__IMPORTANT:__ you may get the following errors while running the script:
```python
import mosketch_for_maya
mosketch_for_maya.install();
// Error: mosketch_for_maya.install(); // 
// Error: Line 2.27: Syntax error //
```
That means that you are in a MEL console. Please switch to a Python console:

![Python Console in Maya](https://user-images.githubusercontent.com/7549728/34869610-b8fb68c0-f787-11e7-9eea-083186c13be8.png)

You should now have a new Shelf called ```MosketchForMaya``` containing several shelfButtons to __Start__, __Stop__, __Load Mosko__ and __Load Okto__.

## Streaming
Follow these steps to start streaming from [Mosketch&trade;](https://www.mokastudio.com) to Maya.

__In [Mosketch&trade;](https://www.mokastudio.com):__ 
1. Import your character
2. Start streaming [(see online help)](http://support.mokastudio.com/support/solutions/articles/6000176455-streaming)

__In Maya:__
1. Import your character
2. Start ```MosketchForMaya``` Python script by pressing ![Start Mosketch for Maya](https://user-images.githubusercontent.com/7549728/28462640-558a38a6-6e1c-11e7-9d34-b466f11eabe6.png)
3. Set IP & press Connect
<p align="center">
<img src ="https://user-images.githubusercontent.com/7549728/28316712-30d73518-6bc4-11e7-8242-6f8fdb1090f2.png" /><br>
Mosketch for Maya GUI
</p>

Now, if you move your character in [Mosketch&trade;](https://www.mokastudio.com), it should also move inside Maya.

__IMPORTANT:__ make sure you start streaming in Mosketch first.

To Stop the ```MosketchForMaya``` Python script, press ![Stop Mosketch for Maya](https://user-images.githubusercontent.com/7549728/28462639-5588ad60-6e1c-11e7-9588-c3878a4c606d.png).

## Limitations
Currently, this script only streams joints values directly on joints. Streaming on FK controllers and rigs is not supported for the moment.

## [Mosketch&trade;](https://www.mokastudio.com)
[Mosketch&trade;](https://www.mokastudio.com) enables the artists to instantly animate any 3D characters - a humanoid, a dog, a dragon, a  tree, anything - simply by sketching or dragging its joints. 
Thanks to [Mosketch&trade;](https://www.mokastudio.com), the artists can now create 3D animations in an easy, fast, and intuitive way.

[![Mosketch Demo](https://user-images.githubusercontent.com/7549728/28310538-137f0656-6bad-11e7-826a-7b971637dbf5.png)](https://player.vimeo.com/video/205231700?autoplay=1)
<p align="center">
<a href="https://vimeo.com/205231700">Mosketch&trade; Video Demo</a>
</p>
