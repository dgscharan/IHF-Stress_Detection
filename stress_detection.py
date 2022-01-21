import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly
import zipfile,fnmatch,os
import flirt.reader.empatica


rootPath = r" "
ZipFolderName = " "
for root, dirs, files in os.walk(rootPath):
    for filename in fnmatch.filter(files, ZipFolderName):
        print(os.path.join(root, filename))
        zipfile.ZipFile(os.path.join(root, filename)).extractall(os.path.join(root, os.path.splitext(filename)[0]))

dir = os.path.splitext(filename)[0]
ibi = pd.read_csv(rootPath+dir+'/IBI.csv')
mean_ibi = ibi[' IBI'].mean()

#extracting features 
ibis = flirt.reader.empatica.read_ibi_file_into_df(rootPath+ dir + '/IBI.csv')
hrv_features = flirt.get_hrv_features(ibis['ibi'], 128, 1, ["td", "fd", "stat"], 0.2)
hrv_features = hrv_features.dropna(how='any',axis=0)
hrv_features.reset_index(inplace=True)

#defining a moving avg for smoothing the curve 
def moving_avarage_smoothing(X,k):
	S = np.zeros(X.shape[0])
	for t in range(X.shape[0]):
		if t < k:
			S[t] = np.mean(X[:t+1])
		else:
			S[t] = np.sum(X[t-k:t])/k
	return S

MAG_K500  = moving_avarage_smoothing(hrv_features['hrv_rmssd'], 500)
hrv_features['MAG_K500'] = MAG_K500
hrv_features.to_csv('hrv_features.csv')
mean_rmssd = hrv_features['hrv_rmssd'].mean()

def Starting_timeStamp(column, time_frames):
    time_index = []
    for i in range(len(column)-1):
        if column[i] < mean_rmssd and column[i+1] > mean_rmssd:
            time_index.append(time_frames[i])
    return time_index

def Ending_timeStamp(column, time_frames):
    time_index = []
    for i in range(len(column)-1):
        if column[i] > mean_rmssd and column[i+1] < mean_rmssd:
            time_index.append(time_frames[i])
    if column[len(column) -1 ] > mean_rmssd:
        time_index.insert(len(time_index), time_frames[len(time_frames) -1])
    else:
        pass        
    return time_index
 
starting_timestamp = Starting_timeStamp(hrv_features['MAG_K500'], hrv_features['datetime'])
ending_timestamp = Ending_timeStamp(hrv_features['MAG_K500'], hrv_features['datetime'])

if starting_timestamp > ending_timestamp:
    temp = starting_timestamp
    starting_timestamp = ending_timestamp
    ending_timestamp = temp
else:
    pass

starting_timestamp_df = pd.DataFrame(starting_timestamp)
ending_timestamp_df = pd.DataFrame(ending_timestamp)
frames = (starting_timestamp_df, ending_timestamp_df)
events_df = pd.concat(frames,  axis=1)
events_df.columns = ['Starting Timestamp', 'Ending Timestamp']
events_df.to_csv(rootPath+"timestamp_" +dir+ ".csv")