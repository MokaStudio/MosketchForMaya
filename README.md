# [Mosketch&trade;](https://www.mokastudio.com) For Maya
```mosketch_for_maya.py``` is a simple Python script allowing you to stream joint values (orientation and translation) from [Mosketch&trade;](https://www.mokastudio.com) to Maya (and vice versa).

## Installation
First, download and copy ```mosketch_for_maya.py``` into your local scripts folder:
* __Windows:__ ```<My Documents>\maya\scripts```
* __MacOSX:__ ```~/Library/Preferences/Autodesk/maya/scripts```

Then, start the script:
```python
import mosketch_for_maya
mosketch_for_maya.start()
```
When you are done, stop the script:
```python
mosketch_for_maya.stop()
```
## Streaming
Follow these steps to start streaming from [Mosketch&trade;](https://www.mokastudio.com) to Maya.

__In [Mosketch&trade;](https://www.mokastudio.com):__ 
1. Import your character
2. Start streaming (see online help).

__In Maya:__
1. Import your character
2. Set IP & press Connect

Now, if you move your character in [Mosketch&trade;](https://www.mokastudio.com), it should also move inside Maya.

## [Mosketch&trade;](https://www.mokastudio.com)
[Mosketch&trade;](https://www.mokastudio.com) enables the artist to instantly animate any 3D characters - a humanoid, a dog, a dragon, a  tree, anything - simply by sketching or dragging its joints. 
Thanks to [Mosketch&trade;](https://www.mokastudio.com), artists can now create 3D animations in an easy, fast, and intuitive way.

[![Mosketch Demo](https://user-images.githubusercontent.com/7549728/28310538-137f0656-6bad-11e7-826a-7b971637dbf5.png)](https://player.vimeo.com/video/205231700?autoplay=1)
<p align="center">
<a href="https://vimeo.com/205231700">Mosketch&trade; Video Demo</a>
</p>
