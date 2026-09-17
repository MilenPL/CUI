# CUI
Clock-like User Interface (made for Linux)

In CUI icons are placed on a disk around the clocks face instead of a convencional and boring taskbar. CUI is an interface made by a 15yo (me). I am working on Arch Linux, but it should work on all linux distros. It works great with KDE Plasma envaierment, idk how it looks like in other DEs. it isn't bootable from the greater as a full DE, it's just a shell (for now; I will make it a full DE in future). i think its a creative idea to make a GUI that instead of taskbars uses circular selection menu. its my first project yet, so i would love to hear some suggestions.

I was helping myself with AI, specificly Gemini, becouse i dont know how to use the PyQt libary. I will learn at some point tho.

required pacages: python, python3, pyqt6, qt5-tools
use this command on archlinux/manjaro/cachyos to install them all:
sudo pacman -S python python3, pyqt6 qt5-tools

Warning! do the things i mention below only if you know what you are doing!
it works only in kde plasma:
if you want to get rid of plasmas start menu under the super (windows) key then use this command in terminal:
plasmashell --replace &
if you want to then get back normal plasma desktop: open terminal and enter: 
plasmashell
do not turn off the terminal yet, wait until its fully loaded and restert your computer.
