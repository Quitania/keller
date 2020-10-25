import sys
import RPi.GPIO as GPIO
import tm1637
from time import sleep
from influxdb import InfluxDBClient

# Configure InfluxDB connection variables
host = "localhost" 
port = 8086 # default port
user = "rpi" # the user/password created for the pi, with write access
password = "rpi" 
dbname = "sensor_data" # the database we created earlier

# Create the InfluxDB client object
Client = InfluxDBClient(host, port, user, password, dbname)

buttonPin = 15

Display = tm1637.TM1637(CLK=23, DIO=24, brightness=1.0)
Display.Clear()

resultSet = Client.query('select mean("temperature") from "rpi-dht22" WHERE time >= now() - 8h')
result = resultSet['rpi-dht22']
temperature = '{:3.2f}'.format(list(result)[0]['mean'])

resultSet = Client.query('select mean("temperature") from "rpi-dht22" WHERE time >= now() - 24h GROUP BY time(6h) LIMIT 4')
results = list(resultSet['rpi-dht22'])
print results
sequence = [row['mean'] for row in results]
minEntry = min(enumerate(results), key=lambda r: r[1]['mean'])
maxEntry = max(enumerate(results), key=lambda r: r[1]['mean']) 
minValue = minEntry[1]['mean']
maxValue = maxEntry[1]['mean']
minIndex = minEntry[0]
maxIndex = maxEntry[0]
difference = (maxValue - minValue) / 3

print minValue, minIndex
print maxValue, maxIndex
print difference

graph = list()
for index in [0, 1, 2, 3]:
    if (index == minIndex):
        graph.append(16)
    elif (index == maxIndex):
        graph.append(18)
    else:
        value = results[index]['mean']
        if (value < (minValue + difference)):
            graph.append(16)
        elif (value > (maxValue - difference)):
            graph.append(18)
        else:
            graph.append(17)

print graph

def button_callback(channel):
    global Display, Client, temperature, graph

    Display.ShowDoublepoint(True)
    Display.Show([int(temperature[0]), int(temperature[1]), int(temperature[3]), int(temperature[4])])
    sleep(2.5)
    Display.ShowDoublepoint(False)
    Display.Show(graph)
    sleep(2.5)
    Display.Clear()

GPIO.setup(buttonPin, GPIO.IN) # Set pin 10 to be an input pin 

GPIO.add_event_detect(buttonPin, GPIO.RISING, callback=button_callback, bouncetime=2000) # Setup event on pin 10 rising edge

message = raw_input("Press enter to quit\n\n") # Run until someone presses enter

Display.Clear()
GPIO.cleanup() # Clean up
