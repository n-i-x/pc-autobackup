# PC AutoBackup for Linux and OS X for Samsung digital cameras #

This project is in active development and is currently a work-in-progress.

If you'd like to donate to the development of PC AutoBackup use the following link:

[![](https://www.paypalobjects.com/en_US/i/btn/btn_donate_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=HRSE2F7539HR8&lc=US&item_name=PC%20AutoBackup%20Development&item_number=pc%2dautobackup&currency_code=USD&bn=PP%2dDonationsBF%3abtn_donate_LG%2egif%3aNonHosted)


---


# Getting Started #

## Requirements ##
  * [Python 2.5+](http://python.org/download/releases/2.7.3/) _Python 3.x not yet tested_
  * [Twisted](http://twistedmatrix.com/trac/wiki/Downloads)

## Configuring your camera ##
> ### If your camera has already been setup with PC AutoBackup for Windows ###
    * Mount your camera's SD card
    * pc_autobackup.py --import_camera_config=/path/to/camera
    * Uninstall PC AutoBackup on Windows **_(failure to do so will prevent this server from working)_**
> ### If you have never setup PC AutoBackup before ###
    * Mount your camera's SD card
    * pc_autobackup.py --create_camera_config=/path/to/camera

## Starting the server ##
  * pc_autobackup.py

> See _pc_autobackup.py --help_ for more options

## **Tested with the following cameras:** ##

  * DV300F
  * NX1000
  * WB150F
  * Does it work with your camera? Send me a pull request editing this README.

## **Tested on the following OS:** ##

  * Ubuntu 12.04 (precise) 32/64-bit
  * Mac OS X 10.8.2 (Mountain Lion)

## **Tested on the following Python versions:** ##

  * Python 2.7.2
  * Python 2.7.3


---

**_This software is NOT created or supported by Samsung_**

**_Samsung is a registered trademark of Samsung Electronics Co., Ltd._**
