"""
Simple HUE Controller v 0.1
Copyright (C)  2019  Zameer Razack

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""


from http.client import HTTPConnection 
import json
import re
import copy
import time

from tkinter import *
from tkinter import messagebox
from tkinter import ttk

light = []

class HUEbridge:
    id = "001788fffe4ee17b"
    internalipaddress = "10.0.0.1"
    username = "nfqxIPSO5dsu8zhsttotKWm0yQJiRttubEiOvhdi"

    @classmethod
    def request(cls, method='GET', url=None, body=None):
        
        # make an HTTP connection to the HUE bridge
        connection = HTTPConnection(cls.internalipaddress)
        connection.request(method, url, body)

        # receive the JSON response from the HUE bridge
        response = connection.getresponse()
        json_object = json.loads(response.read().decode())

        return json_object


class Light:

    def __init__(self, light_id, state):
        self._light_id = light_id
        self._state = state

    def __str__(self):
        return json.dumps(self._state, indent=4)

    # getter method
    def getState(self):
        return self._state['state']
    
    def setHue(self, bri = "default", hue = "default", sat = "default", transitiontime=4):

        if bri == "default": bri = self._state['state']['bri']
        if hue == "default": hue = self._state['state']['hue']
        if sat == "default": sat = self._state['state']['sat']
        
        color_settings = {
            "bri": bri,
            "hue": hue,
            "sat": sat,
            "transitiontime": transitiontime
        }

        sethue_address = "/api/" + str(HUEbridge.username) + "/lights/" + str(self._light_id) + "/state"        
        response = HUEbridge.request(method = 'PUT', url = sethue_address, body=json.dumps(color_settings))

        # The below Regex instruction produces a list of tuples:
        # tuple[1] = success, tuple[2] = name of the setting, tuple[3] = value of that setting
        successes = re.findall(r'(success).*?(hue|sat|bri|transitiontime).*?[^/]([0-9]{1,})', json.dumps(response))
        
        # Update the values of this light instance
        for tuple in successes:
            self._state['state'][tuple[1]] = int(tuple[2])
            
        # Check for errors
        if len(successes) < 3:
            errors = re.findall(r'(error).*?(hue|sat|bri|transitiontime).*?"description": "(.*?)"', json.dumps(response))
            print(errors)

  
    def switch(self):

        switch_setting = { "on": not self._state['state']['on'] }
        
        switch_address = "/api/" + str(HUEbridge.username) + "/lights/" + str(self._light_id) + "/state"        
        response = HUEbridge.request(method = 'PUT', url = switch_address, body=json.dumps(switch_setting))
        
        success = re.findall(r'(success).*?(on).*?(True|true|False|false)', json.dumps(response))

        if len(success) == 1:
            if str(success[0][2]).lower() == 'true': self._state['state']['on'] = True
            else: self._state['state']['on'] = False
        else:
            print(success) # print the error


class View:
        
    def __init__(self, master):
           
        # Create arrays for the light controller frames 
        self.lightcontroller = [0 for x in range(len(light))]

        self.briSlider =  [0 for x in range(len(light))]
        self.hueSlider =  [0 for x in range(len(light))]
        self.satSlider =  [0 for x in range(len(light))]

        self.briSliderValue = [0 for x in range(len(light))]

        self.briEntry =  [0 for x in range(len(light))]
        self.hueEntry =  [0 for x in range(len(light))]
        self.satEntry =  [0 for x in range(len(light))]

        self.briEntryText = [0 for x in range(len(light))]
        self.hueEntryText = [0 for x in range(len(light))]
        self.satEntryText = [0 for x in range(len(light))]

        self.on_off_button = [0 for x in range(len(light))]
        self.selectedLight = [0 for x in range(len(light))]
        
        # Selection frame
        selection_frame = ttk.LabelFrame(master, height = 100, width = 156, text = "Selection")
        
        # Cycle Selected Lights button
        self.Button_CycleSelectedLights = ttk.Button(selection_frame, text = "Cycle Selected Lights", width = 21, command = self._cycleSelectedLights)
        self.Button_CycleSelectedLights.grid(row = 0, column = 0, columnspan = 2, padx = 5, pady = 5)

        # Cycle continuously value and cycle_continuously_value variable
        ttk.Label(selection_frame, text="Cycle continuously").grid(row = 1, column = 0, pady = 2, sticky = W)

        self.cycle_continuously_value = 0
        self.Button_CycleContinuously = ttk.Button(selection_frame, text = "Off", width=4, command = self._updateContinuousCycleButton)
        self.Button_CycleContinuously.grid(row = 1, column = 1, padx = 5, pady = 2)

        # Transition time entry box
        ttk.Label(selection_frame, text="Transition time:").grid(row = 2, column = 0, pady = 2, sticky = W)
        
        self.transitionTimeText = StringVar()
        ttk.Entry(selection_frame, width=4, textvariable = self.transitionTimeText).grid(row = 2, column = 1, padx = 5, pady = 2)
        self.transitionTimeText.set(4)

        selection_frame.pack(side=LEFT, anchor=N, padx = 5, pady = 5)

        # Light controllers
        for light_id in range(len(light)):

            # Create a unique frame name
            light_controller_name = "Light " + str(light[light_id]._light_id)
            self.lightcontroller[light_id] = ttk.LabelFrame(master, height = 200, width = 100, text = light_controller_name)
            
            # Create Brightness controls
            ttk.Label(self.lightcontroller[light_id], text = "Brightness").grid(row = 0, column = 0)
            
            bri_slider_name = "bri" + str(light_id)
            self.briSlider[light_id] = ttk.Scale(   self.lightcontroller[light_id], 
                                                    orient =  VERTICAL, 
                                                    length = 254, from_ = 254, to = 0,
                                                    command=lambda value, 
                                                    name=bri_slider_name: self._sendToLight(name, value)
                                                )
            self.briSlider[light_id].grid(row = 1, column = 0)
            
            self.briEntryText[light_id] = StringVar()
            self.briEntry[light_id] = ttk.Entry(self.lightcontroller[light_id], width=5, textvariable=self.briEntryText[light_id])
            self.briEntry[light_id].grid(row = 2, column = 0, pady= 10)

            # Create Hue controls
            ttk.Label(self.lightcontroller[light_id], text = "Hue").grid(row = 0, column = 1)
            
            hue_slider_name = "hue" + str(light_id)
            self.hueSlider[light_id] = ttk.Scale(   self.lightcontroller[light_id], 
                                                    orient =  VERTICAL, 
                                                    length = 254, from_ = 65536, to = 0, 
                                                    command=lambda value, 
                                                    name=hue_slider_name: self._sendToLight(name, value)
                                                )
            self.hueSlider[light_id].grid(row = 1, column = 1)

            self.hueEntryText[light_id] = StringVar()
            self.hueEntry[light_id] = ttk.Entry(self.lightcontroller[light_id], 
                                                width=5, 
                                                textvariable=self.hueEntryText[light_id]
                                               )
            self.hueEntry[light_id].grid(row = 2, column = 1, pady= 10)

            # Create Saturation controls
            ttk.Label(self.lightcontroller[light_id], text = "Saturation").grid(row = 0, column = 2)
            
            sat_slider_name = "sat" + str(light_id)
            self.satSlider[light_id] = ttk.Scale(   self.lightcontroller[light_id], 
                                                    orient =  VERTICAL, 
                                                    length = 254, from_ = 254, to = 0, 
                                                    command=lambda value, 
                                                    name=sat_slider_name: self._sendToLight(name, value)
                                                )            
            self.satSlider[light_id].grid(row = 1, column = 2)

            self.satEntryText[light_id] = StringVar()
            self.satEntry[light_id] = ttk.Entry(self.lightcontroller[light_id], 
                                                width=5, 
                                                textvariable=self.satEntryText[light_id]
                                               )
            self.satEntry[light_id].grid(row = 2, column = 2, pady= 10)

            # Create Selection checkboxes
            self.selectedLight[light_id] = IntVar()
            ttk.Checkbutton(self.lightcontroller[light_id], 
                            text = "Select", 
                            variable=self.selectedLight[light_id]).grid(row = 3, column = 0, columnspan = 2, pady= 10)
            
            # Create On/Off button
            self.on_off_button[light_id] = ttk.Button(  self.lightcontroller[light_id], 
                                                        text = "On", width=4, 
                                                        command= lambda button_id=light_id: self._switchOnOffButton(button_id)
                                                     )
            self.on_off_button[light_id].grid(row = 3, column = 2, pady= 10)

            # Add light controller to parent
            self.lightcontroller[light_id].pack(side=LEFT, padx = 5, pady = 5)

    
    def _sendToLight(self, slider_name, value):

        list_of_values = re.split(r'(bri|hue|sat)([0-9]*)', slider_name)
        value = int(float(value))
        light_id = int(list_of_values[2])

        if list_of_values[1] == 'bri': 
            self.briEntryText[light_id].set(str(value))
            light[light_id].setHue(bri = value)

        elif list_of_values[1] == 'hue': 
            self.hueEntryText[light_id].set(str(value))
            light[light_id].setHue(hue = value)

        elif list_of_values[1] == 'sat': 
            self.satEntryText[light_id].set(str(value))
            light[light_id].setHue(sat = value)


    def _cycleSelectedLights(self):

        selected_lights = []

        for i in range(len(light)):
            selected = self.selectedLight[i].get()
            if selected : selected_lights.append(i)
        
        if len(selected_lights) < 2:
            messagebox.showinfo("Cycle Selected Lights", "Please select two or more lights to use this function")
            return False

        transition_time = int(float(self.transitionTimeText.get()))

        cycle(selected_lights, transition_time)


    def _updateContinuousCycleButton(self):
        ''' This function updates the continuous cycle value, button text, 
            and triggers the continuous cycle loop self._executeContinuousCycle().
        '''

        if self.cycle_continuously_value == 0:
            self.Button_CycleContinuously.config(text = "On")
            self.cycle_continuously_value = 1

            # Execute __executeContinuousCycle() and set button to Off and value to 0
            # if that function fails.
            if self._executeContinuousCycle() == False:
                self.Button_CycleContinuously.config(text = "Off")
                self.cycle_continuously_value = 0

        else: 
            self.Button_CycleContinuously.config(text = "Off")
            self.cycle_continuously_value = 0


    def _executeContinuousCycle(self):
        ''' This function is solely called by _updateContinuousCycleButton().
            The purpose of this subroutine is that it will call itself when 
            self.cycle_continuously_value is 1.
        '''
        
        if self.cycle_continuously_value == 1:
            
            # Execute _cycleSelectedLights() and return False if that function fails.
            if self._cycleSelectedLights() == False: return False
            
            transition_time = int(float(self.transitionTimeText.get()))
            cycle_time = transition_time * 100
            self.Button_CycleContinuously.after(cycle_time, self._executeContinuousCycle)


    def _switchOnOffButton(self, light_id):
        
        light_state = light[light_id].getState()

        if light_state['on'] == True:
            self.on_off_button[light_id].config(text = "Off")
            light[light_id].switch()
        else:
            self.on_off_button[light_id].config(text = "On")
            light[light_id].switch()


def lightfactory():
    
    all_light_states_address = "/api/" + str(HUEbridge.username) + "/lights"
    all_light_states = HUEbridge.request(url = all_light_states_address)

    # create instances of class Light() in array light[] using the key and values in the all_light_states JSON object
    for key, value in all_light_states.items():
        light_id = int(key)
        light.append(Light(light_id, value))
    

def cycle(lights, transitiontime=4):

# read_lights into light_state_buffer{light_id, value}, write_lights to setHue() 

    if len(lights) < 2:
        print("Cycle requires a list with two or more items")
        return

    slice_at_position = len(lights) - 1
    buffer_target_positions = lights[slice_at_position:] + lights[:slice_at_position]

    buffer_light = {}

    head_position = 0
    while head_position < len(lights):
        light_id = buffer_target_positions[head_position]
        buffer_light[head_position] = copy.deepcopy(light[light_id].getState())

        head_position = head_position + 1

    head_position = 0
    while head_position < len(lights):
        light_id = lights[head_position]
        light[light_id].setHue( buffer_light[head_position]['bri'], 
                                buffer_light[head_position]['hue'], 
                                buffer_light[head_position]['sat'], 
                                transitiontime )
        
        head_position = head_position + 1


def main():
    lightfactory()
    root = Tk()
    root.wm_title("Simple HUE Controller v0.1")
    display_on_screen = View(root)
    root.mainloop()


if __name__ == "__main__": main()
