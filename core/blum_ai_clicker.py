# Standard Libraries
from typing import Tuple, Dict
from math import sqrt
from time import sleep

# Third-party Libraries
from pynput.mouse import Button, Controller
import cv2 as cv
import keyboard

# Custom Modules
from core.window_capture import WindowCapture
from core.image_processor import ImageProcessor
from utils import console_utils

mouse = Controller()


class BlumAIClicker:
    def start(self):
        window_name = "Blum1"
        cfg_file_name = "./yolov4-tiny/yolov4-tiny-custom.cfg"
        weights_file_name = "yolov4-tiny-custom_last.weights"

        # Create necessary class objects
        wincap = WindowCapture(window_name)
        image_size = wincap.get_window_size()
        improc = ImageProcessor(image_size, cfg_file_name, weights_file_name)

        # Set target games count
        games_to_play = console_utils.ask_how_much_games_to_play()
        games_played = 0

        print(f"Games goal for this session is set to {games_to_play} games.")
        print("Please, open Blum home page and focus on it. Starting AI clicker in 5 seconds...")
        sleep(5)

        while games_played < games_to_play:
            print(f"New game started! ({games_played}/{games_to_play})")

            # Step #1.1: Start game window capture
            ss = wincap.get_screenshot()

            # Step #1.2: Quick game if needed
            if keyboard.is_pressed('q'):
                print("You exited the script!")
                break

            # Step #1.3: Get all detected objects with their coordinates
            coordinates = improc.proccess_image(ss)

            # Step #2.1: Get play button
            play_buttons = [c for c in coordinates if c["class_name"] in ["play_btn", "play_again_btn"]]
            if len(play_buttons) > 0:
                # Step #1: Get play button coordinates and size
                play_btn = play_buttons[0]
                play_btn_x = play_btn['x']
                play_btn_y = play_btn['y']
                btn_w = play_btn['w']
                btn_h = play_btn['h']

                # Step #2: Locate x, y for btn
                btn_center_coordinates = self._find_object_center(x=play_btn_x, y=play_btn_y, width=btn_w, height=btn_h)
                btn_center_x = btn_center_coordinates['x']
                btn_center_y = btn_center_coordinates['y']

                # Step #3: Press play btn and increase played games counter
                self.click_at(x=btn_center_x, y=btn_center_y)
                games_played += 1

            # Step #2.2: Filter in-game objects
            stars_and_freezes = [c for c in coordinates if c["class_name"] in ["star", "freeze"]]
            bombs = [c for c in coordinates if c["class_name"] == "bomb"]

            # Priority to "freeze"
            if any(c["class_name"] == "freeze" for c in stars_and_freezes):
                detected_object = next(c for c in stars_and_freezes if c["class_name"] == "freeze")
            else:
                detected_object = stars_and_freezes[0] if stars_and_freezes else None

            if detected_object:
                # Step #1: Get coordinates and parameters of the detected object
                obj_x = detected_object['x']
                obj_y = detected_object['y']
                obj_width = detected_object['w']
                obj_height = detected_object['h']

                # Step #2: Get center coordinates of the detected object
                obj_center_coordinates = self._find_object_center(x=obj_x, y=obj_y, width=obj_width, height=obj_height)
                obj_center_x = obj_center_coordinates['x']
                obj_center_y = obj_center_coordinates['y']

                # Step #3: Scale coordinates to screen resolution
                image_width, image_height = image_size
                scaled_center_coordinates = self._convert_coordinates(x=obj_center_x, y=obj_center_y,
                                                                      initial_width=image_width,
                                                                      initial_height=image_height,
                                                                      target_width=2560, target_height=1440)
                scaled_x, scaled_y = scaled_center_coordinates

                # Check if the detected object is near a bomb
                too_close_to_bomb = False
                for bomb in bombs:
                    bomb_center_coordinates = self._find_object_center(x=bomb['x'], y=bomb['y'], width=bomb['w'],
                                                                       height=bomb['h'])
                    if self.distance(obj_center_coordinates, bomb_center_coordinates) < max(obj_width, obj_height):
                        too_close_to_bomb = True
                        break

                # Click only if it's not too close to a bomb
                if not too_close_to_bomb:
                    self.click_at(scaled_x, scaled_y)

        print('Finished.')

    @staticmethod
    def _find_object_center(x: int, y: int, width: int, height: int) -> dict:
        center_x = x + width / 2
        center_y = y + height / 2

        center_coordinates = {
            'x': center_x,
            'y': center_y
        }

        return center_coordinates

    @staticmethod
    def _convert_coordinates(x: int, y: int, initial_width: int, initial_height: int, target_width: int,
                             target_height: int) -> Tuple[int, int]:
        """
        Convert coordinates from one resolution to another.

        Parameters:
        x, y: Coordinates in the initial resolution.
        initial_width, initial_height: Dimensions of the initial resolution.
        target_width, target_height: Dimensions of the target resolution.

        Returns:
        (target_x, target_y): Coordinates in the target resolution.
        """
        # Calculate scaling factors
        scale_x = target_width / initial_width
        scale_y = target_height / initial_height

        # Apply scaling to coordinates
        target_x = x * scale_x
        target_y = y * scale_y

        return int(target_x), int(target_y)

    @staticmethod
    def distance(coord1: dict, coord2: dict) -> float:
        """Calculate the Euclidean distance between two coordinates."""
        distance = sqrt((coord1['x'] - coord2['x']) ** 2 + (coord1['y'] - coord2['y']) ** 2)
        return distance

    @staticmethod
    def click_at(x: int, y: int) -> None:
        """Move the mouse to the specified coordinates and click."""
        mouse.position = (x, y)
        mouse.press(Button.left)
        sleep(0.05)
        mouse.release(Button.left)
