# weather_icons.py 
# This module defines 8x8 pixel art icons for various weather conditions using RGB color tuples.


# Define RGB colors 

B = (0, 0, 0)          # Black 
W = (255, 255, 255)    # White 
O = (255, 165, 0)      # Orange 
G = (64, 64, 64)       # Gray 
T = (0, 128, 128)      # Teal 

 

# Clear Sky Day (01d) 

clear_sky_day_icon = [ 
    B, B, B, B, B, B, B, B,  
    B, B, O, O, O, O, B, B, 
    B, O, O, O, O, O, O, B, 
    B, O, O, O, O, O, O, B, 
    B, O, O, O, O, O, O, B, 
    B, O, O, O, O, O, O, B, 
    B, B, O, O, O, O, B, B, 
    B, B, B, B, B, B, B, B 
] 

 

# Few Clouds Day (02d) 

few_clouds_day_icon = [ 
    B, B, B, B, B, B, B, B, 
    B, B, B, B, O, O, B, B, 
    B, B, B, O, O, O, O, B, 
    B, B, W, W, W, O, O, B, 
    B, W, W, W, W, W, B, B, 
    B, W, W, W, W, W, W, B, 
    B, B, B, B, B, B, B, B, 
    B, B, B, B, B, B, B, B 
]  

 

# Scattered Clouds Day (03d) 

scattered_clouds_day_icon = [ 
    B, B, B, B, B, B, B, B, 
    B, B, B, B, B, B, B, B, 
    B, B, W, W, B, B, B, B, 
    B, B, W, W, W, B, B, B, 
    B, W, W, W, W, W, B, B, 
    B, W, W, W, W, W, W, B, 
    B, B, B, B, B, B, B, B, 
    B, B, B, B, B, B, B, B 
] 

 

# Broken Clouds Day (04d) 

broken_clouds_day_icon = [ 
    B, B, B, B, B, B, B, B, 
    B, B, B, G, G, B, B, B, 
    B, B, W, W, G, G, B, B, 
    B, B, W, W, W, G, G, B, 
    B, W, W, W, W, W, G, B, 
    B, W, W, W, W, W, W, B, 
    B, B, B, B, B, B, B, B, 
    B, B, B, B, B, B, B, B 
] 

 

# Shower Day (09d) 

shower_day_icon = [ 
    B, B, B, B, B, B, B, B, 
    B, B, B, G, G, B, B, B, 
    B, B, W, W, G, G, B, B, 
    B, B, W, W, W, G, G, B, 
    B, W, W, W, W, W, G, B, 
    B, W, W, T, W, T, W, B, 
    B, B, T, B, T, B, B, B,  
    B, B, B, B, B, B, B, B 
] 

 

# Rain Day (10d) 

rain_day_icon = [ 
    B, B, B, B, B, B, B, B, 
    B, B, B, B, O, O, B, B, 
    B, B, B, O, O, O, O, B, 
    B, B, W, W, W, O, O, B, 
    B, W, W, W, W, W, B, B, 
    B, W, W, T, W, T, W, B, 
    B, B, T, B, T, B, B, B,  
    B, B, B, B, B, B, B, B 
] 

 

# Thunderstorm Day (11d) 

thunderstorm_day_icon = [ 
    B, B, B, B, B, B, B, B, 
    B, B, B, G, G, B, B, B, 
    B, B, W, W, G, G, B, B, 
    B, B, W, W, W, G, G, B, 
    B, W, O, W, W, W, G, B, 
    B, W, O, O, W, W, W, B, 
    B, B, B, O, B, B, B, B, 
    B, B, B, B, B, B, B, B 
] 

 

# Snow Day (13d) 

snow_day_icon = [ 
    B, B, B, B, B, B, B, B, 
    B, B, T, B, T, B, T, B, 
    B, B, B, B, B, T, B, B, 
    B, T, B, B, T, B, T, B, 
    B, B, B, B, B, B, B, B, 
    B, B, T, B, B, B, T, B, 
    B, B, B, B, T, B, B, B, 
    B, T, B, B, B, B, B, B 
] 

 

# Mist Day (50d) 

mist_day_icon = [ 
    B, B, B, B, B, B, B, B, 
    B, G, G, B, G, G, G, B, 
    B, B, B, B, B, B, B, B, 
    B, G, G, G, G, G, B, B, 
    B, B, B, B, B, B, B, B, 
    B, G, G, G, B, B, B, B, 
    B, B, B, B, B, G, G, B, 
    B, B, B, B, B, B, B, B 
] 
 


clear_sky_night_icon = [ 
    B, B, B, B, B, B, B, B,  
    B, B, G, G, G, G, B, B, 
    B, G, G, G, G, G, G, B, 
    B, G, G, G, G, G, G, B, 
    B, G, G, G, G, G, G, B, 
    B, G, G, G, G, G, G, B, 
    B, B, G, G, G, G, B, B, 
    B, B, B, B, B, B, B, B 
] 

 

# Few Clouds Night (02d) 

few_clouds_night_icon = [ 
    B, B, B, B, B, B, B, B, 
    B, B, B, B, G, G, B, B, 
    B, B, B, G, G, G, G, B, 
    B, B, W, W, W, G, G, B, 
    B, W, W, W, W, W, B, B, 
    B, W, W, W, W, W, W, B, 
    B, B, B, B, B, B, B, B, 
    B, B, B, B, B, B, B, B 
]  

 

# Scattered Clouds Night (03d) 

scattered_clouds_night_icon = [ 
    B, B, B, B, B, B, B, B, 
    B, B, B, B, B, B, B, B, 
    B, B, W, W, B, B, B, B, 
    B, B, W, W, W, B, B, B, 
    B, W, W, W, W, W, B, B, 
    B, W, W, W, W, W, W, B, 
    B, B, B, B, B, B, B, B, 
    B, B, B, B, B, B, B, B 
] 

 

# Broken Clouds Night (04d) 

broken_clouds_night_icon = [ 
    B, B, B, B, B, B, B, B, 
    B, B, B, G, G, B, B, B, 
    B, B, W, W, G, G, B, B, 
    B, B, W, W, W, G, G, B, 
    B, W, W, W, W, W, G, B, 
    B, W, W, W, W, W, W, B, 
    B, B, B, B, B, B, B, B, 
    B, B, B, B, B, B, B, B 
] 

 

# Shower Night (09d) 

shower_night_icon = [ 
    B, B, B, B, B, B, B, B, 
    B, B, B, G, G, B, B, B, 
    B, B, W, W, G, G, B, B, 
    B, B, W, W, W, G, G, B, 
    B, W, W, W, W, W, G, B, 
    B, W, W, T, W, T, W, B, 
    B, B, T, B, T, B, B, B,  
    B, B, B, B, B, B, B, B 
] 

 

# Rain Night (10n) 

rain_night_icon = [ 
    B, B, B, B, B, B, B, B, 
    B, B, B, B, G, G, B, B, 
    B, B, B, G, G, G, G, B, 
    B, B, W, W, W, G, G, B, 
    B, W, W, W, W, W, B, B, 
    B, W, W, T, W, T, W, B, 
    B, B, T, B, T, B, B, B,  
    B, B, B, B, B, B, B, B 
] 

 

# Thunderstorm Night (11n) 

thunderstorm_night_icon = [ 
    B, B, B, B, B, B, B, B, 
    B, B, B, G, G, B, B, B, 
    B, B, W, W, G, G, B, B, 
    B, B, W, W, W, G, G, B, 
    B, W, O, W, W, W, G, B, 
    B, W, O, O, W, W, W, B, 
    B, B, B, O, B, B, B, B, 
    B, B, B, B, B, B, B, B 
] 

 

# Snow Night (13n) 

snow_night_icon = [ 
    B, B, B, B, B, B, B, B, 
    B, B, T, B, T, B, T, B, 
    B, B, B, B, B, T, B, B, 
    B, T, B, B, T, B, T, B, 
    B, B, B, B, B, B, B, B, 
    B, B, T, B, B, B, T, B, 
    B, B, B, B, T, B, B, B, 
    B, T, B, B, B, B, B, B 
] 

 

# Mist Night (50n) 

mist_night_icon = [ 
    B, B, B, B, B, B, B, B, 
    B, G, G, B, G, G, G, B, 
    B, B, B, B, B, B, B, B, 
    B, G, G, G, G, G, B, B, 
    B, B, B, B, B, B, B, B, 
    B, G, G, G, B, B, B, B, 
    B, B, B, B, B, G, G, B, 
    B, B, B, B, B, B, B, B 
] 



# Icon map 

icon_map = { 
    "01d": clear_sky_day_icon, 
    "02d": few_clouds_day_icon, 
    "03d": scattered_clouds_day_icon, 
    "04d": broken_clouds_day_icon, 
    "09d": shower_day_icon, 
    "10d": rain_day_icon, 
    "11d": thunderstorm_day_icon, 
    "13d": snow_day_icon, 
    "50d": mist_day_icon,
    "01n": clear_sky_night_icon, 
    "02n": few_clouds_night_icon, 
    "03n": scattered_clouds_night_icon, 
    "04n": broken_clouds_night_icon, 
    "09n": shower_night_icon, 
    "10n": rain_night_icon, 
    "11n": thunderstorm_night_icon, 
    "13n": snow_night_icon, 
    "50n": mist_night_icon 
} 



# Example usage with Sense HAT
# This part of the code demonstrates how to display the icons on a Sense HAT one icon at a time for 10 seconds each.
# Unciomment to run.


# from sense_hat import SenseHat
# import time
#
# sense = SenseHat()
# for code, icon in icon_map.items():
#     sense.clear()
#     sense.set_pixels(icon)
#     time.sleep(3)
# sense.clear()
