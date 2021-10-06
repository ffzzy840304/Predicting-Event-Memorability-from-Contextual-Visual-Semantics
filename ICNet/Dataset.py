import torch.utils.data as data
from PIL import Image
import os
import os.path
import numpy as np

import operator
from scipy import stats
import csv
from sklearn.preprocessing import MinMaxScaler
import torch

img_extensions = ['.jpg', '.png', '.jpeg']
class ICset(data.Dataset):
    def __init__(self, img_root='', split_root='', split='train_1', demo=False, transform=None,target_transform=None):
        self.img_root = os.path.expanduser(img_root)
        self.transform = transform
        self.target_transform = target_transform
        self.split = split
        self.image_cache = None
        self.valid_labels = False
        
        self.split_file=os.path.join(split_root,split)
        self.csv_file=os.path.join(split_root,split)
        if not os.path.isdir(self.split_file):
            fname, ext = os.path.splitext(self.split_file)
            if ext == '':
                self.split_file += '.txt'  
                self.csv_file += '.csv'
        self.data = []
        self.features=[]
        self.labels = []
        
        if demo==True:
           # Load imaegs from given directory
            image_names = sorted(os.listdir(self.split_file))
            #print(image_names)
            print("Loaded",len(image_names),'images from directory',self.split_file)
            index=self.split_file.rfind('/')
            split_index=self.split_file[index-1:index]
            #print(self.split_file)
            images = []
            for img_name in image_names:
                full_img_path = os.path.join(self.split_file, img_name)
                if not os.path.isfile(full_img_path):
                    continue

                gt_label = 0
                file, ext = os.path.splitext(img_name)
                if ext.lower() in img_extensions:
                    self.data.append(full_img_path)

                    # Set default ground truth memorabiltiy. This Could be extracted form the image filename
                    self.labels.append(float(gt_label))
                    f=open('/path/to/datasets/r3/splits/'+'val_'+split_index+'.txt')
                    lines=f.readlines()
                    count=0
                    image_id=0
                    for line in lines:
                        spt=line.split(' ')
                        if spt[0]==img_name:
                           image_id=count
                           break
                        count=count+1
                    with open('/path/to/datasets/r3/splits/split_name/'+'val_'+split_index+'.csv', 'r') as file:
                         reader = csv.reader(file)
                         counter=0
                         for row in reader:
                             if counter==image_id+1:
                                self.features.append(row[1:-1])
                                break
                             counter=counter+1
           # print(self.features[0])
            scaler = MinMaxScaler()
            self.features=scaler.fit_transform(self.features)
        else:
             # Load images according to a split file
            with open(self.split_file, 'rt') as f:
                for line in f:
                    parts = line.strip().split(' ')
                    img_filename = parts[0].strip()
                    full_img_path = os.path.join(self.img_root, img_filename)
                    if os.path.isfile(full_img_path):
                        self.data.append(full_img_path)
                        self.labels.append(float(parts[1].strip())*10)
                        self.valid_labels = True
                    else:
                        print ("WARNING image ", full_img_path," doesn't exist")
            with open(self.csv_file, 'r') as file:
                 reader = csv.reader(file)
                 counter=0
                 for row in reader:
                   if counter>=1:
                      self.features.append(row[1:-1])           
                   counter=counter+1
            scaler = MinMaxScaler()
            self.features=scaler.fit_transform(self.features)
        
        return
     # Loads image from file and returns BGR
    def img_loader(self, path, RGB=False):

        if self.image_cache is not None:
            img = self.image_cache.get_image(path)
            if img is not None:
                return img
        
        with open(path, 'rb') as f:
            with Image.open(f) as img:
                img_out = img.convert('RGB')
                if self.image_cache is not None:
                    self.image_cache.cache_image(path, img_out)

                return img_out

    
    def preload_images(self):
        # Preload images
        if self.image_cache is not None:
            for path in self.data:
                self.img_loader(path)


    def __getitem__(self, index):
        sample = self.img_loader(self.data[index])
        features=self.features[index]
     
        target = self.labels[index]

        if self.transform is not None:
            sample = self.transform(sample)

  
        features=np.array(features)
        features=torch.from_numpy(features.astype(float)).float()
      
        if self.target_transform is not None:
            target = self.target_transform(target)
        

        return sample, features, target, self.data[index]


    def __len__(self):
        return len(self.data)
 
