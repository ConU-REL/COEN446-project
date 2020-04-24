# COEN 446 MQTT Project

## Smart HVAC System

### Installation Steps
The steps for installing this project are listed in the project report.

### Project Breakdown
This project involves the design and implementation of a simple MQTT system which automatically controls the temperature within a home or room based upon the preferences of the users that occupy that home or room.


### Entities that must be designed:
#### 1. Management App
  - MQTT Publisher
  - Simple user input frontend
    - Takes "Name" and "Preferred Temperature" as user input, publishes to Broker

#### 2. Smart Door Locker
  - MQTT Publisher
  - Simple user input frontend
  - Publishes to the Broker whenever somebody enters the house
    - People entering the house will be simulated simply by passing the name of the person entering the house to this entitiy

#### 3. Connected Thermostat
  - MQTT Subscriber
  - Responsible for setting the temperature in the house based on the people present in the house
  - Sets temperature to 15 &deg;C if the house is empty
  - If house is not empty:
    - If only one person in the house:
      - Temperature is set to the preference the person in the house
    - If multiple people in the house:
      - Temperature is set to the preference of the first person that arrived.
      - If the first person leaves, the next person's preference will be chosen.


### MQTT Implementation Description

The MQTT Broker and Client we designed operate over UDP. Our implementation only uses QoS 0, and has no "retain" functionality. However, these flags have been included for the sake of correctness.

The following messages have been implemented:

1. Conect
   
   Contains the header "CONNECT" with no content
2. Connack
   
   Contains the header "ACK" with no content
3. Publish
   
   Contains header "PUB", then the Topic to publish to, the QoS level, the Retain flag, and the actual message content
4. Subscribe
   
   Contains the header "SUB" followed by a list of topics to subscribe to
5. Suback
   
   Contains the header "ACK" with the content "SUB" followed by a list of return values for all of the requesed subscription topics
6. Unsubscribe
   
   Contains the header "UNSUB" followed by a list of topics to unsubscribe from
7. Unsuback
   
   Contains the header "ACK" with the content "UNSUB"
8. Disconnect
   
   Contains the header "DISC" and no further content

These messages should be more than sufficient for basic MQTT communication.