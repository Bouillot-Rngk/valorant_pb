# valorant_pb

# Purpose

This tool is meant to manage a Valorant Series and display meaningful information like Team Names, Logos, Pick & Ban maps and Series Score during broadcast. \
As of today, this tool support only a Best Of 3 series and do not handle multiple teams. No information is stored, it only travel through websockets, no redux, no database. 

# Installation 

This tool as only be used and tested on Windows10 and higher. There is no plan to support other Operating Systems. \
This tool works with Flask, and HTML/CSS/JS pages

## Requirements 
Python >= 3.10 

## Clone the repository

```bash
cd Place/You/Want/Your/Folder
git clone https://github.com/Bouillot-Rngk/valorant_pb.git
cd valorant_pb
```

## Setting up a Virtual Environnement 
### Create a Python virtual environnement
```git
python -m venv pb_valo
```

### Activate the Python virtual environnement and install dependencies
#### Windows PowerShell
```bash
pb_valo\Scripts\Activate
```
#### Git Bash
```bash
source pb_valo\Scripts\Activate
```

#### Install Dependencies
```bash
python -m pip install -r requirements.txt
```

## Launch the tool 
```bash
python app.py
```

## Using the tool 

#### Control Panel : 127.0.0.1:5000 
#### Pick et Ban maps: 127.0.0.1:5000/overlay
#### Agent Select overlay: 127.0.0.1:5000/score_overlay
#### In Game BO Tracking and scores: 127.0.0.1:5000/bo_tracking
