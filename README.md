# Brugmelding – Home Assistant Integratie

Deze integratie haalt actuele brugstatussen op van:

http://brugmelding.svenkopp.com/get/bruggen_open.json

Je kunt tijdens het toevoegen van de integratie een brug selecteren.  
Elke brug verschijnt daarna als sensor met state `true` (open) of `false` (dicht).

De integratie maakt een apparaat aan per gekozen brug, met een eigen icoon.
