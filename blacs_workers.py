#####################################################################
#                                                                   #
# /labscript_devices/AndorSolis/blacs_workers.py                    #
#                                                                   #
# Copyright 2019, Monash University and contributors                #
#                                                                   #
# This file is part of labscript_devices, in the labscript suite    #
# (see http://labscriptsuite.org), and is licensed under the        #
# Simplified BSD License. See the license.txt file in the root of   #
# the project for the full license.                                 #
#                                                                   #
#####################################################################
from zprocess import rich_print
from labscript_devices.IMAQdxCamera.blacs_workers import MockCamera, IMAQdxCameraWorker

class InsituAnalysisCameraWorker(IMAQdxCameraWorker):

    def __init__():
        super().__init__(interface_class)
        self.interface_class = interface_class

    def transition_to_buffered(self, device_name, h5_filepath, initial_values, fresh):
        if getattr(self, 'is_remote', False):
            h5_filepath = path_to_local(h5_filepath)
        if self.continuous_thread is not None:
            # Pause continuous acquistion during transition_to_buffered:
            self.stop_continuous(pause=True)
        with h5py.File(h5_filepath, 'r') as f:
            group = f['devices'][self.device_name]
            if not 'EXPOSURES' in group:
                return {}
            self.h5_filepath = h5_filepath
            self.exposures = group['EXPOSURES'][:]
            self.n_images = len(self.exposures)
            self.actions = self.exposures[:,4]
            
            # Get the camera_attributes from the device_properties
            properties = labscript_utils.properties.get(
                f, self.device_name, 'device_properties'
            )
            camera_attributes = properties['camera_attributes']
            self.stop_acquisition_timeout = properties['stop_acquisition_timeout']
            self.exception_on_failed_shot = properties['exception_on_failed_shot']
            saved_attr_level = properties['saved_attribute_visibility_level']
        # Only reprogram attributes that differ from those last programmed in, or all of
        # them if a fresh reprogramming was requested:
        if fresh:
            self.smart_cache = {}
        self.set_attributes_smart(camera_attributes)
        # Get the camera attributes, so that we can save them to the H5 file:
        if saved_attr_level is not None:
            self.attributes_to_save = self.get_attributes_as_dict(saved_attr_level)
        else:
            self.attributes_to_save = None
        print(f"Configuring camera for {self.n_images} images.")
        self.camera.configure_acquisition(continuous=False, bufferCount=self.n_images)
        self.images = []
        self.acquisition_thread = threading.Thread(
            target=self.camera.grab_multiple,
            args=(self.n_images, self.images, self.actions),
            daemon=True,
        )
        self.acquisition_thread.start()
        return {}