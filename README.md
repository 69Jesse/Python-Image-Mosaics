# Python-Image-Mosaics

Image to Mosaic generator written in Python.

It mostly uses PIL and Numpy so it is actually pretty efficient.

How to use:
- You input your mosaics in the folder `/mosaics` (in this case they are images from the game Minecraft.)
- You input your images you want converted in the folder `/input`
- You change the variables `GRID_SIZE` (longest side of the output image) and `CELL_SIZE` (longest side of the mosaic image) to your liking
- You run `main.py` and wait for that to finish
- Look at your results in the folder `/output`

Example output with GRID_SIZE=1024, CELL_SIZE=16 and Minecraft mosaics:
![guccitwig 1676946168](https://user-images.githubusercontent.com/104533077/220235214-ba29d057-3355-4c5d-bbd8-128838541531.png)

![guccitwig](https://user-images.githubusercontent.com/104533077/220236226-ff7e6a34-6e88-4dd5-a244-1137aca6e960.png)

Image in `/input` ^
