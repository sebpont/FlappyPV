// this code gets the arduino to read three anolgue signals and print out the values. 
// the python code checks for line 'v' then reads the next three lines as it's contoller inputs for 'bird', 'cat', and 'dog'.

void setup() 
{
  Serial.begin(9600);
}

void loop() 
{
  Serial.println("v");
  int sensorValue0 = analogRead(A0);
  Serial.println(sensorValue0);
  int sensorValue1 = analogRead(A1);
  Serial.println(sensorValue1);
  int sensorValue2 = analogRead(A2);
  Serial.println(sensorValue2);
  delay(50);
}
