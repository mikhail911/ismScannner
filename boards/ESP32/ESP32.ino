/*
ESP32ISM24Scanner.ino - Copyright (C) 2018 by Michał Stojke
This code allows to scan with ESP32: Wi-Fi networks and
Bluetooth devices working on ISM 2.4GHz band, and send
collected data to PC application by serial port.
*/

#include <Arduino.h>
#include <BLEAdvertisedDevice.h>
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEScan.h>
#include "WiFi.h"

// Init global variables
String this_board_name = "ESP32", board_name;
bool start_reading_conf = false, wifi_scan = true, blue_scan = false, start_scanning = false;
int time_interval = 10000;
int scanTime = 2;

class DiscoveredDevicesData : public BLEAdvertisedDeviceCallbacks
{
  void onResult(BLEAdvertisedDevice discoveredDevice)
  {
    // Data template: DEV | Name | RSSI | MAC |
    //Serial.printf("Advertised Device: %s", discoveredDevice.toString().c_str());
    if (discoveredDevice.haveName())
    {
      Serial.printf("DEV | %s |", discoveredDevice.getName());
    }
    else
    {
      Serial.printf("DEV | N/A | ");
    }
    Serial.printf(discoveredDevice.getAddress().toString().c_str());
    if (discoveredDevice.haveRSSI())
    {
      Serial.printf(" | %d | ", (int)discoveredDevice.getRSSI());
    }
    char *pHex = BLEUtils::buildHexData(nullptr, (uint8_t *)discoveredDevice.getManufacturerData().data(), discoveredDevice.getManufacturerData().length());
    Serial.printf(pHex);
    Serial.printf("\n");
  }
};

void startScanningBluetooth()
{
  Serial.println("[MSG] Start reading BLE devices");
  BLEScan *pBLEScan = BLEDevice::getScan(); //create new scan
  pBLEScan->setAdvertisedDeviceCallbacks(new DiscoveredDevicesData());
  pBLEScan->setActiveScan(false); //active scan uses more power, but get results faster
  pBLEScan->setInterval(0x50);
  pBLEScan->setWindow(0x30);
  BLEDevice::init("ESP32");
  Serial.println("[SCN]BLUE_START_SCAN");
  BLEScanResults foundDevices = pBLEScan->start(scanTime);
  Serial.println("[SCN]BLUE_STOP_SCAN");
}

String encryptionTypeName(int x)
{
  switch (x)
  {
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

void setup()
{
  Serial.begin(9600);
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  delay(100);
  Serial.println("[SYS]Board started");
}

void loop()
{
  String command;
  if (Serial.available() > 0)
  {
    command = Serial.readStringUntil('\n');
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
    if (blue_scan == true)
    {
      startScanningBluetooth();
    }
    delay(time_interval);
  }
}