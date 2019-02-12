/*
  ESP8266ISM24Scanner.ino - Copyright (C) 2018 by Michał Stojke
  This code allows to scan with ESP8266 Wi-Fi networks and
  send collected data to PC application by serial port.
*/

#include <Arduino.h>
#include "ESP8266WiFi.h"

// Init global variables
String this_board_name = "ESP8266", board_name;
bool start_reading_conf = false, wifi_scan = true, blue_scan = false, start_scanning = false;
int time_interval = 10000;

void setup() {
  Serial.begin(9600);
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  delay(100);
  Serial.println("[SYS]Board started");
}

String encryptionTypeName(int x) {
  switch (x) {
    case 2:
      return "WPA";
      break;
    case 4:
      return "WPA2";
      break;
    case 5:
      return "WEP";
      break;
    case 7:
      return "NONE";
      break;
    case 8:
      return "AUTO";
      break;
    default:
      return "NotDetected";
      break;
  }
}

void startScanningWifi()
{
  Serial.println("[SYS]Start scanning Wi-Fi networks");

  int n = WiFi.scanNetworks();
  Serial.println("[SYS]Scan done");
  if (n == 0)
  {
    Serial.println("[SYS]No networks found");
  }
  else
  {
    // No | Name | RSSI | Channel | Encryption | MAC | isHidden
    Serial.println("[SCN]WIFI_START_SCAN");
    for (int i = 0; i < n; ++i)
    {
      Serial.print(i + 1);
      Serial.print(" | ");
      Serial.print(WiFi.SSID(i));
      Serial.print(" | ");
      Serial.print(WiFi.RSSI(i));
      Serial.print(" | ");
      Serial.print(WiFi.channel(i));
      Serial.print(" | ");
      Serial.print(encryptionTypeName(WiFi.encryptionType(i)));
      Serial.print(" | ");
      Serial.print(WiFi.BSSIDstr(i));
      Serial.println(" | ");
    }
  }
  Serial.println("[SCN]WIFI_STOP_SCAN");
}

void loop()
{
  String command;
  if (Serial.available() > 0)
  {
    command = Serial.readStringUntil('\n');
    Serial.print("received: ");
    Serial.println(command);
    if (command == "[CFG]START" && start_reading_conf == false)
    {
      start_reading_conf = true;
      Serial.println("[SYS]Start receiving configuration");
    }
    else if (command != "[CFG]STOP" && start_reading_conf == true)
    {
      if (command == "[CFG]BOARD=" + this_board_name)
      {
        board_name = command;
        Serial.println("[CFG]OK");
      }
      else if (command == "[CFG]WIFI_SCAN=TRUE")
      {
        wifi_scan = true;
        Serial.println("[CFG]Wi-Fi scan enabled");
      }
      else if (command == "[CFG]WIFI_SCAN=FALSE")
      {
        wifi_scan = false;
        Serial.println("[CFG]Wi-Fi scan disabled");
      }
      else if (command.startsWith("[CFG]TIME"))
      {
        command.remove(0, 10);
        time_interval = command.toInt();
        Serial.println("[CFG]Time interval configuration succeeded");
      }
      // ESP32 (only):
      else if (command == "[CFG]BLUE_SCAN=TRUE")
      {
        blue_scan = true;
        Serial.println("[CFG]Bluetooth scan enabled");
      }
      else if (command == "[CFG]BLUE_SCAN=FALSE")
      {
        blue_scan = false;
        Serial.println("[CFG]Bluetooth scan disabled");
      }
      else if (command != "[CFG]BOARD=" + this_board_name)
      {
        Serial.println("[CFG]BOARD_ERROR");
        start_reading_conf = false;
      }
    }
    else if (command == "[CFG]STOP")
    {
      start_reading_conf = false;
      Serial.println("[SYS]Stopped receiving configuration");
    }
    else if (command == "[SCN]START")
    {
      start_scanning = true;
      Serial.println("[SYS]Scanning started");
      startScanningWifi();
    }
    else if (command == "[SCN]STOP")
    {
      start_scanning = false;
      Serial.println("[SYS]Scanning stopped!");
    }
  }
  else if (start_scanning == true)
  {
    startScanningWifi();
    delay(time_interval);
  }
}
