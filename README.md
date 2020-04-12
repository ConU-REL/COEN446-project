# COEN 446 MQTT Project

## Smart HVAC System

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