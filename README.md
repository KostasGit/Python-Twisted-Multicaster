# Python-Twisted-Multicaster
A simple python peer based on the twisted framework. More info in the README.

*This is a modified version of an example file that was part of a Distributed Systems project.*

How to run (in this order-you can modify it to work with any port):

py multicast.py 0 127.0.0.1:2109

py multicast.py 1 127.0.0.1:2109

py multicast.py 2 127.0.0.1:2109

This simple implementation of a totally ordered multicasting (with lamport clocks) is made possible by running 3 peers on the same machine.
The code is pretty self-explainatory, but i'll try my best to break it down into steps.

Main:
1. Create the peerfactory
2. Listen to the given ports for a connection
3. Make the connections 
4. Run the reactor and wait for messages

After it makes the connections, each peer multicasts 20 messages.

