![Mosketch for Maya](https://user-images.githubusercontent.com/7549728/28314038-58406cb0-6bb9-11e7-87bc-47d7f9e3d46d.png)

# [Mosketch&trade;](https://www.mokastudio.com) for Maya
```mosketch_for_maya.py``` is a simple Python script showcasing how to stream joints values (orientation and translation) from [Mosketch&trade;](https://www.mokastudio.com) to Maya (and vice versa). You need to start [streaming in Mosketch](http://support.mokastudio.com/support/solutions/articles/6000176455-streaming) first.

Feel free to adapt it and port it to any other software.

Please note that the main purpose is to keep the script as short and simple as possible.

## Installation
First, download and copy ```mosketch_for_maya.py``` into your local scripts folder:
* __Windows:__ ```<My Documents>\maya\scripts```
* __MacOSX:__ ```~/Library/Preferences/Autodesk/maya/scripts```

Then, start the script (with the [Script Editor](https://knowledge.autodesk.com/support/maya/learn-explore/caas/CloudHelp/cloudhelp/2017/ENU/Maya/files/GUID-7C861047-C7E0-4780-ACB5-752CD22AB02E-htm.html) a [shelf button](https://knowledge.autodesk.com/support/maya/learn-explore/caas/CloudHelp/cloudhelp/2017/ENU/Maya/files/GUID-58C25080-5864-4709-BE3A-0543E9D1FCF2-htm.html)):
```python
import mosketch_for_maya
mosketch_for_maya.start()
```
You can use the Script Editor or put the Python lines above in a shelf button. For more information, please refer to Maya's documentation.

When you are done, stop the script:
```python
mosketch_for_maya.stop()
```
## Streaming
Follow these steps to start streaming from [Mosketch&trade;](https://www.mokastudio.com) to Maya.

__In [Mosketch&trade;](https://www.mokastudio.com):__ 
1. Import your character
2. Start streaming [(see online help)](http://support.mokastudio.com/support/solutions/articles/6000176455-streaming)
<p align="center">
<img src="https://user-images.githubusercontent.com/7549728/28316205-250e77ac-6bc2-11e7-9bb2-3d3d1ef05582.png" /><br>
Streaming Properties in Mosketch
</p>

__In Maya:__
1. Import your character
2. Set IP & press Connect
<p align="center">
<img src ="https://user-images.githubusercontent.com/7549728/28316712-30d73518-6bc4-11e7-8242-6f8fdb1090f2.png" /><br>
Mosketch for Maya GUI
</p>

Now, if you move your character in [Mosketch&trade;](https://www.mokastudio.com), it should also move inside Maya.

__WARNING: make sure you start streaming in Mosketch first.__

## [Mosketch&trade;](https://www.mokastudio.com)
[Mosketch&trade;](https://www.mokastudio.com) enables the artists to instantly animate any 3D characters - a humanoid, a dog, a dragon, a  tree, anything - simply by sketching or dragging its joints. 
Thanks to [Mosketch&trade;](https://www.mokastudio.com), the artists can now create 3D animations in an easy, fast, and intuitive way.

[![Mosketch Demo](https://user-images.githubusercontent.com/7549728/28310538-137f0656-6bad-11e7-826a-7b971637dbf5.png)](https://player.vimeo.com/video/205231700?autoplay=1)
<p align="center">
<a href="https://vimeo.com/205231700">Mosketch&trade; Video Demo</a>
</p>
