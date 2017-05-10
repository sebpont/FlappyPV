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
