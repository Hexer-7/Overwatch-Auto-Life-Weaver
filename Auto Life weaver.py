# Import necessary libraries
try:
    import sys
    import time
    import cv2
    import mss
    import numpy as np
    import keyboard
    from pynput.mouse import Listener
    import threading
    import os
    import xml.etree.ElementTree as ET
    import subprocess
    from PIL import Image
    from xml.dom import minidom

except ImportError as e:
    import subprocess

    # Install required packages using subprocess if not found
    subprocess.call(['pip', 'install', 'mss'])
    subprocess.call(['pip', 'install', 'opencv-python'])
    subprocess.call(['pip', 'install', 'keyboard'])
    subprocess.call(['pip', 'install', 'pynput'])
    subprocess.call(['pip', 'install', 'numpy'])

    import time
    import cv2
    import mss
    import numpy as np
    import keyboard
    from pynput.mouse import Listener
    import threading
    import os
    import xml.etree.ElementTree as ET
    from PIL import Image
    from xml.dom import minidom

    # Initialize global variables
is_stop = False
is_run = False
locations_array = []

def create_default_config():
    root = ET.Element("config")
    comment = ET.Comment("this button for toggle pause code.")
    root.append(comment)
    pause_toggle_button = ET.SubElement(root, "pause_toggle_button")
    pause_toggle_button.text = "f2"
    heal_btn = ET.SubElement(root, "heal_btn")
    heal_btn.text = current_key('Press \033[0;33mHeal Button (Primary weapon)\033[0m: ','\033[0;33m')
    comment = ET.Comment("this is resolution of game,[2160,1440,1080,768]")
    root.append(comment)
    resolution = ET.SubElement(root, "resolution")
    resolution.text = display_resolutions()



    xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="    ")

    with open("config.xml", "w") as xml_file:
        xml_file.write(xml_str)


def read_config():
    tree = ET.parse("config.xml")
    root = tree.getroot()

    pause_toggle_button = root.find("pause_toggle_button").text
    heal_btn = root.find("heal_btn").text
    selected_resolution = root.find("resolution").text

    return heal_btn,selected_resolution,pause_toggle_button


# Function to display available resolutions and get user input
def display_resolutions():
    os.system('cls')
    print("""
    \033[0;31mImportant\033[0;0m:
        you have to set the game on Fullscreen if have troubles with Auto Life weaver

    Now you have to Choose the Resolution of your game
        4K = 2160
        2K = 1440
        FHD = 1080
        HD+ = 768

    """)
    print("Choose a Resolution:")
    resolutions = ["2160", "1440", "1080", "768"]
    for i, res in enumerate(resolutions, start=1):
        print(f"{i}. \033[0;32m{res}\033[0;0m")
    selected_resolution_index = int(input("Enter the number of your choice: "))
    selected_resolution = resolutions[selected_resolution_index - 1]
    os.system('cls')
    return selected_resolution


# Function to load information from an XML file based on the selected resolution
def load_info_from_xml(resolution):
    xml_path = os.path.join('data', resolution, "info.xml")

    if not os.path.exists(xml_path):
        print(f"Error: Missing info.xml file in {resolution} folder.")
        return None

    tree = ET.parse(xml_path)
    root = tree.getroot()

    res_element = root.find("res")
    locations_element = root.find("locations")

    if res_element:
        high = int(res_element.find("high").text)
        width = int(res_element.find("width").text)
        x = int(res_element.find("x").text)
        y = int(res_element.find("y").text)
        threshold = float(res_element.find("threshold").text)

        # Read locations and add them to the array
        for coord_element in locations_element.findall("coord"):
            x_coord = int(coord_element.get("x"))
            y_coord = int(coord_element.get("y"))
            locations_array.append((x_coord, y_coord))

        return high, width, x, y,threshold

    print(f"Error: Information for resolution {resolution} not found.")
    return None

def current_key(text,color):
    text_button = """
    Now you have to add heal button

    Add an extra button next to the mouse button in the game;

    \033[31mit should not be the mouse button itself.\033[0m

    Like: p or 4 or f4 or anything you want

    see github page for more information @Hexer-7
                """
    print(text_button)
    print(text)
    while True:
        event = keyboard.read_event()

        if event.event_type == keyboard.KEY_DOWN:
            if event.name == 'enter':
                # for skip enter button
                input()
                os.system('cls')
                return current_key
            current_key = event.name
            sys.stdout.write('\r' + ' [ '+ f'{color}{current_key}\033[0m' +' ]'+' ' * 10 + '\r')
            sys.stdout.flush()



# Mouse click callback function to update global variables based on button press/release events
def on_click(x, y, button, pressed):
    global is_run, is_stop
    if not is_stop:
        if button == button.left:
            if pressed:
                is_run = True
            else:
                is_run = False



# Function to start a listener thread for mouse clicks
def start_listener():
    with Listener(on_click=on_click) as listener:
        listener.join()




# Function to print the state of the Auto Life weaver (Running/Stopped)
def print_state():
    global is_stop
    message = '    Auto Life weaver is \033[31mStopped\033[0m' if is_stop else '    Auto Life weaver is \033[32mRunning\033[0m'
    sys.stdout.write('\r' + message + ' ' * (len(message) - len('    Auto Life weaver is stopped')) + '\r')
    sys.stdout.flush()


# Function to filter the input image based on a target color
def filter_color(image,mask_width,mask_high):


    # Ensure the image is in BGR format
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    lower = np.array([240, 240, 240])
    upper = np.array([255, 255, 255])

    mask = cv2.inRange(image, lower, upper)
    image = cv2.bitwise_and(image, image, mask=mask)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY)

    image_mask = create_shaded_image(locations_array,mask_width,mask_high)

    # Convert the shaded image to a binary mask
    image_mask = cv2.cvtColor(np.array(image_mask), cv2.COLOR_RGBA2GRAY)

    _, image_mask = cv2.threshold(image_mask, 0, 250, cv2.THRESH_BINARY)
    image = cv2.bitwise_and(image, image, mask=image_mask)

    return image


# Function to create a shaded image based on a list of coordinates
def create_shaded_image(locations_array,mask_width,mask_high):
    image = Image.new('RGBA', (mask_width, mask_high), (0, 0, 0, 0))
    shaded_pixels = locations_array

    for pixel in shaded_pixels:
        image.putpixel((pixel[0], pixel[1]), (255, 255, 255, 0))
    return image

# Function to continuously capture the screen, analyze images, and perform actions
def capture_screen(health_image):
    global is_run, is_stop
    health_image = cv2.imread(health_image)
    health_image = cv2.resize(health_image, (width, high))
    health_image = filter_color(health_image,width, high)
    health_image = health_image.astype(np.uint8)
    last_action_time = time.time()
    region = {'left': x, 'top': y, 'width': width, 'height': high}

    with mss.mss() as sct:
        while True:

            if not is_run:
                keyboard.release(heal_btn)
                while not is_run:
                    if keyboard.is_pressed('f2'):
                        is_stop = not is_stop
                        print_state()
                        while keyboard.is_pressed('f2'):
                            time.sleep(0.01)
                    time.sleep(0.07)
            if is_stop:
                continue
            keyboard.press(heal_btn)
            img = np.array(sct.grab(region))
            img = cv2.resize(img, (width, high))
            color_filtered_binary = filter_color(img,width, high)
            color_filtered_binary = color_filtered_binary.astype(np.uint8)
            result = cv2.matchTemplate(color_filtered_binary, health_image, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            current_time = time.time()
            time_difference = current_time - last_action_time
            if time_difference >= 0.1:
                if (max_val > threshold):
                    keyboard.release(heal_btn)
                    last_action_time = current_time
                    time.sleep(0.04)



# Main script
if __name__ == "__main__":

    text = f"""

    Auto life weaver is completely free and open source on github @Hexer-7.

    \033[32mFor reset config file, Delete it.\033[0m

    If you have any feedback, contact me on my Instagram DM (_1_B).
    
    
    Press ENTER to continue.
    """
    print(text)
    input()

    if not os.path.isfile("config.xml"):
            create_default_config()

    # Read config values
    heal_btn,selected_resolution,pause_toggle_button = read_config()
    info = load_info_from_xml(selected_resolution)
    if info:
        high, width, x, y, threshold = info
        os.system('cls')

        mouse_listener_thread = threading.Thread(target=start_listener)
        mouse_listener_thread.start()

        print(f'    Now you can Run Auto Life weaver by Holding "Mouse left click"')
        print(f'    and you can toggle pause Auto Life weaver with "{pause_toggle_button}"\n')
        print_state()
        capture_screen(f'data/{selected_resolution}/counter.png')
    else:
        print("Error: Resources not found!")

