import napari
import os
from magicgui.widgets import create_widget, Container
from napari.utils.notifications import show_info
import scipy.ndimage as ndi
from os import listdir
import skimage
import numpy as np
from os.path import isfile, join
import time
from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QProgressBar,
    QSpinBox,
    QFormLayout,
    QComboBox,
    QFileDialog,
    QLineEdit,
    QCheckBox,
    QDial,
    QSlider,
    QComboBox,
    QGridLayout
)


class GUI_widget(QWidget):
   def __init__(self, napari_viewer):
        super().__init__()
        
        self.backup_im = None
        self.label = 1
        self.three_dim = False
        #keep track of whether the dialog is hidden or not

        self.my_spin_box = QSpinBox()

        self.my_spin_box.setValue(25)

        self.viewer = napari_viewer
               
        self.setLayout(QVBoxLayout())
        self.setMaximumWidth(500)
        
     
            
     
        #Add Label Button
        self.my_button = QPushButton('Add Label')
        self.my_button.clicked.connect(self.add_label)
        
        #undo button
        self.btn_undo = QPushButton('Undo')
        self.btn_undo.clicked.connect(self.undo)
        
        
        #text input
        self.my_line_edit = QLineEdit()


        #combobox with some random items
        self.my_combobox = QComboBox()

        self.three_dim_checkbox = QCheckBox('3D flood fill')
    
        self.my_combobox.currentTextChanged.connect(self.change_label)
        
      


        mywidget = QWidget()
        formLayout = QFormLayout()
        formLayout.addRow('Tolerance', self.my_spin_box) 
        formLayout.addRow('', self.three_dim_checkbox)      
        
        formLayout.addRow('New Label Name', self.my_line_edit)
        formLayout.addRow('', self.my_button)      

        formLayout.addRow('Current Label', self.my_combobox)
        formLayout.addRow('Undo', self.btn_undo)
     
    

        mywidget.setLayout(formLayout)
        self.layout().addWidget(mywidget)
        
        
        self.labDict = {}
      
   
        self.viewer.bind_key('f', self.flood_fill)
   

   def undo(self, viewer):
        lab_layer = self.viewer.layers['myLabels']
        lab_layer.data = self.backup_im
   
   def change_label(self, viewer):
        
               
        lab_name = self.my_combobox.currentText()
        print(lab_name)
        for key in self.labDict.keys():
            if key == lab_name:
                self.label = self.labDict[key]
        lab_layer = self.viewer.layers['myLabels']
        
   
   def add_label(self, viewer):
               
        lab = self.my_line_edit.text()
        
        all_labels = [self.my_combobox.itemText(i) for i in range(self.my_combobox.count())]
        if lab not in all_labels:
            self.my_combobox.addItem(lab)
            current_max_lab = self.getCurrentMaxLab()
            print(f'current max lab is {current_max_lab}')
            self.labDict[lab] = current_max_lab + 1 
            print('------keys in dict------')
            for key in self.labDict.keys():
                print(key)
                print(self.labDict[key])
            self.my_combobox.setCurrentText(lab)
        else:
            show_info(f'Error: label {lab} already exists')
  
            
    
   def getCurrentMaxLab(self):
        maxLab = 1
        if len(self.labDict.keys()) > 0:
            for key in self.labDict.keys():
                if self.labDict[key] > maxLab:
                    maxLab = self.labDict[key]
            return maxLab
        else:
            return 0
        

   def flood_fill(self, viewer):
        
        
       
        tol = self.my_spin_box.value()
        layer = self.viewer.layers[0]
        im = layer.data
          
        labels_exists = False
        for layer in viewer.layers:
            if str(layer) == 'myLabels':
                labels_exists = True
                
         
        if not labels_exists:
            labels = np.zeros(im.shape, dtype=np.uint8)
            viewer.add_labels(labels, name='myLabels')
            
            
        lab_layer = viewer.layers['myLabels']
        labs = lab_layer.data
           
        self.backup_im = np.copy(labs)
        
        pos = self.viewer.cursor.position 
        pos_image = layer.world_to_data(pos) 
        if len(im.shape) == 2:
            flood = skimage.segmentation.flood(im, (int(pos_image[0]), int(pos_image[1])), tolerance=tol)
            flood = ndi.binary_fill_holes(flood)
            labs[flood == 1] = self.label        
            lab_layer.data = labs
        elif len(im.shape) == 3:
       
            if self.three_dim_checkbox.isChecked():
                flood = skimage.segmentation.flood(im, (int(pos_image[0]), int(pos_image[1]), int(pos_image[2])), tolerance=tol)
                flood = ndi.binary_fill_holes(flood)
                labs[flood == 1] = self.label        
                lab_layer.data = labs
            else:
                pos = viewer.dims.current_step[0]
                im_single = im[pos,:,:]
                flood = skimage.segmentation.flood(im_single, (int(pos_image[1]), int(pos_image[2])), tolerance=tol)                
                flood = ndi.binary_fill_holes(flood)
                labs[pos,:,:][flood == 1] = self.label        
                lab_layer.data = labs
        
        else:
            show_info('only 2 and 3d images supported')
        
        
        
        
        
        
       
        
        #self.viewer.add_labels(labs, blending='additive')
        
    
   #functions to connect to the various widgets
   
        
        

                  
   def spinbox_changed(self):
        show_info(f'spinbox changed to {self.my_spin_box.value()}')
            
   def open_file_dialog(self):
        #default path is current working dir
        foldername = os.getcwd()
        self.my_file_dialogue = QFileDialog()
        self.my_file_dialogue.setFileMode(QFileDialog.Directory)
        
        if self.my_file_dialogue.exec_():
            foldername = self.my_file_dialogue.selectedFiles()
        
        
        self.my_combobox.clear()
        onlyfiles = [os.path.join(foldername[0], f) for f in listdir(foldername[0]) if isfile(os.path.join(foldername[0], f))]
        for file in onlyfiles:
            self.my_combobox.addItem(file)
        
   def open_file(self):
        filepath = self.my_combobox.currentText()
        image = skimage.io.imread(filepath)
        self.viewer.add_image(image)
            
            
            
if __name__ == "__main__":

    # create a Viewer
    viewer = napari.Viewer()

    # add our plugin
    viewer.window.add_dock_widget(GUI_widget(viewer))

    napari.run()