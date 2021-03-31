"""
    Tests a pre-trained DNN model
"""

import time
import copy
import torch
import numpy as np
from tqdm.autonotebook import tqdm as tqdm
from torch.utils.tensorboard import SummaryWriter

from model_taxinet import TaxiNetDNN, freeze_model
from taxinet_dataloader import *
from plot_utils import *

# make sure this is a system variable in your bashrc
NASA_ULI_ROOT_DIR=os.environ['NASA_ULI_ROOT_DIR']

DATA_DIR = NASA_ULI_ROOT_DIR + '/data/'

# where intermediate results are saved
# never save this to the main git repo
SCRATCH_DIR = NASA_ULI_ROOT_DIR + '/scratch/'

UTILS_DIR = NASA_ULI_ROOT_DIR + '/src/utils/'
sys.path.append(UTILS_DIR)

from textfile_utils import *

def test_model(model, dataset, dataloader, device, loss_func):
    
    dataset_size = len(dataset)
    
    losses = []
    times_per_item = []
    loss_name = "loss"
    
    # Iterate over data.
    for inputs, labels in tqdm(dataloader):
        inputs = inputs.to(device)
        labels = labels.to(device)
    
        # forward
        # track history if only in train
        start = time.time()
        outputs = model(inputs)
        end = time.time()
        
        times_per_item.append( (end - start)/inputs.shape[0] )
        
        loss = loss_func(outputs, labels).mean()
 
        losses.append( loss.cpu().detach().numpy() )

    results = {
        "loss_name": loss_name,
        "losses": np.concatenate(losses),
        "time_per_item": np.mean(times_per_item),
        "time_per_item_std": np.std(times_per_item) / np.sqrt(dataset_size),
    }
        
    return results


if __name__=='__main__':

    torch.cuda.empty_cache()
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    print('found device: ', device)

    # where the training results should go
    results_dir = remove_and_create_dir(SCRATCH_DIR + '/test_DNN_taxinet/')

    # where raw images and csvs are saved
    BASE_DATALOADER_DIR = DATA_DIR + 'nominal_conditions'

    test_dir = BASE_DATALOADER_DIR + '_test/'

    dataloader_params = {'batch_size': 512,
                         'shuffle': False,
                         'num_workers': 12,
                         'drop_last': False}

    # MODEL
    # instantiate the model 
    model = TaxiNetDNN()

    # load the pre-trained model

    # DATALOADERS
    # instantiate the model and freeze all but penultimate layers
    test_dataset = TaxiNetDataset(test_dir)

    test_loader = DataLoader(test_dataset, **dataloader_params)

    # LOSS FUNCTION
    loss_func = torch.nn.MSELoss().to(device)

    # DATASET INFO
    datasets = {}
    datasets['test'] = test_dataset

    dataloaders = {}
    dataloaders['test'] = test_loader

    # TEST THE DNN
    test_results = test_model(model, test_dataset, test_loader, device, loss_func)
