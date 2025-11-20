from django.db import models

class WeatherData(models.Model):
    city = models.CharField(max_length=100)
    temperature = models.FloatField()
    humidity = models.FloatField()
    wind_speed = models.FloatField()
    air_quality = models.FloatField()
    precipitation = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def str(self):
        return self.city