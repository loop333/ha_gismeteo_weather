# Gismeteo.ru Home Assistant Weather Component

place in ./homeassistant/custom_components/weather  

config:  

```
weather:
  - platform: gismeteo
    name: any_optional_name
    city: 4517
    mode: hourly|daily
```

city code - number at end of url, for example:  
https://www.gismeteo.ru/weather-yekaterinburg-4517/
