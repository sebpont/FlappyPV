# FlappyPV

Hello!! Thanks for visiting

This is a project to build a game coded in python, running on a Raspberry Pi and, most importantly, the controller input is with a solar panel (i.e. more light, more votlage, bird goes up; less light, less voltage, bird goes down). It was built for as an science outreach project to be played at Imperial Festival as a way to engage children in the solar cell reserach undertaken at Imperial College London. It's programmed to take three 0-5 V inputs that control three players on the continuous flappy bird type game. 

Hardware:
  - 5 V solar panel, up to three (e.g. http://uk.rs-online.com/web/p/photovoltaic-solar-panels/6646778/)
  - Arduino Uno (or alternative anaolgue to serial microcontroller) (http://uk.rs-online.com/web/p/processor-microcontroller-development-kits/7154081/)
  - Raspberry Pi 3 (earlier versions won't be able to handle to the graphics of the game) (http://uk.rs-online.com/web/p/processor-microcontroller-development-kits/8968660/)
  - Standard accessories for Raspberry Pi (screen, keyboard, mouse, SD card)
  
Schematic:
 1. solar panel gives 0-5 V analogue signal
 2. arduino converts analogue input to serial output
 3. raspbery pi reads serial data and runs python scripted game

What to do:
  1. Program ardunio on standard laptop or desktop and upload FlappyPV/FlappyPV_Arduino_code.ino 
  2. Start up and load Raspberry Pi
  3. Download and run FlappyPV/GameTest_3playerWithSolar.py
  
Notes:
This is my first experience with a RPi and pygame. The code is not as effective as it could be but worked for what we needed.
To get the RPi to handle the game there are some curious edits in the code.

The game is heavily based off the example below.
https://codereview.stackexchange.com/questions/61477/flappy-bird-game-clone-for-a-beginners-programming-class/61570
But it has been greatly updated now, none of which has been added to this version yet.
https://github.com/TimoWilken/flappy-bird-pygame/blob/master/flappybird.py

Help starting the arduino:
https://www.arduino.cc/en/Guide/HomePage

Help connecting arduino to pi:
https://www.raspberrypi.org/blog/raspberry-pi-and-arduino/
 
 
