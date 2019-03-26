# Gismeteo.ru Home Assistant Weather Component

```sh
cd ~/.homeassistant/custom_components  
git clone https://github.com/loop333/ha_gismeteo_weather gismeteo
```
configuration.yaml:  
```yaml
weather:
  - platform: gismeteo
    name: any_optional_name
    city: 4517
    mode: hourly|daily
```

city code - number at end of url, for example 4517 in:  
https://www.gismeteo.ru/weather-yekaterinburg-4517/
